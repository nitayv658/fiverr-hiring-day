import os
import time
from decimal import Decimal
from celery_app import celery
from app import db, Click, Link, Reward, app


@celery.task(name='tasks.process_reward')
def process_reward_task(click_id, seller_id, link_id, amount):
    """Celery task to process rewards via Bedrock or local mock."""
    try:
        bedrock_url = os.getenv('BEDROCK_CREDIT_URL')
        bedrock_token = os.getenv('BEDROCK_BEARER_TOKEN')

        aws_txn_id = None
        remote_status = 'completed'

        if bedrock_url and bedrock_token:
            try:
                import requests

                headers = {
                    'Authorization': f'Bearer {bedrock_token}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'seller_id': seller_id,
                    'amount': float(amount),
                    'link_id': link_id,
                    'click_id': click_id
                }
                resp = requests.post(bedrock_url, json=payload, headers=headers, timeout=5)
                if 200 <= resp.status_code < 300:
                    try:
                        resp_json = resp.json()
                        aws_txn_id = resp_json.get('transaction_id') or resp_json.get('transactionId')
                    except Exception:
                        aws_txn_id = None
                    remote_status = 'completed'
                else:
                    remote_status = 'failed'
            except Exception as e:
                print(f'Bedrock call failed: {e}')
                remote_status = 'failed'
        else:
            # local mock latency
            time.sleep(0.05)

        with app.app_context():
            reward = Reward(
                seller_id=seller_id,
                link_id=link_id,
                click_id=click_id,
                amount=Decimal(str(amount)),
                status=remote_status,
                aws_transaction_id=aws_txn_id
            )
            db.session.add(reward)

            click = db.session.get(Click, click_id)
            if click:
                click.reward_status = remote_status

            link = db.session.get(Link, link_id)
            if link and remote_status == 'completed':
                link.credits_earned = Decimal(str(link.credits_earned)) + Decimal(str(amount))

            db.session.commit()
    except Exception as e:
        print(f'Celery reward task error: {e}')
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            pass
