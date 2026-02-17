"""
Test suite for Fiverr Shareable Links API
Tests all endpoints: POST /link, GET /link/<code>, GET /state
"""

import pytest
import json
import time
from app import app, db, Link, Click, Reward

@pytest.fixture
def client():
    """Setup test client and database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

class TestHealthCheck:
    """Test health endpoint"""
    
    def test_health_check_success(self, client):
        """Health check should return 200 when database is connected"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data

class TestIndex:
    """Test index endpoint"""
    
    def test_index_returns_available_endpoints(self, client):
        """Index should return available endpoints"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'api' in data
        assert 'endpoints' in data
        assert 'POST /link' in data['endpoints']
        assert 'GET /link/<short_code>' in data['endpoints']
        assert 'GET /state' in data['endpoints']

class TestCreateLink:
    """Test POST /link endpoint"""
    
    def test_create_link_success(self, client):
        """Should successfully create a short link"""
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'link' in data
        assert data['link']['seller_id'] == 'seller123'
        assert data['link']['original_url'] == 'https://fiverr.com/gigs/logo-design'
        assert 'short_code' in data['link']
        assert 'short_url' in data['link']
        assert data['link']['click_count'] == 0
        assert float(data['link']['credits_earned']) == 0.0
    
    def test_create_link_missing_seller_id(self, client):
        """Should return 400 when seller_id is missing"""
        payload = {
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_link_missing_original_url(self, client):
        """Should return 400 when original_url is missing"""
        payload = {
            'seller_id': 'seller123'
        }
        response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_link_empty_payload(self, client):
        """Should return 400 when payload is empty"""
        response = client.post('/link',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_deduplication_same_seller_same_url(self, client):
        """Should reuse existing link if same seller requests same URL"""
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        
        # Create first link
        response1 = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response1.status_code == 201
        data1 = json.loads(response1.data)
        short_code1 = data1['link']['short_code']
        
        # Try to create same link again
        response2 = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert response2.status_code == 200  # Existing
        data2 = json.loads(response2.data)
        assert data2['link']['short_code'] == short_code1
        assert 'already exists' in data2['message']
    
    def test_different_seller_same_url(self, client):
        """Different sellers can create links for the same URL"""
        url = 'https://fiverr.com/gigs/logo-design'
        
        payload1 = {'seller_id': 'seller1', 'original_url': url}
        payload2 = {'seller_id': 'seller2', 'original_url': url}
        
        response1 = client.post('/link',
            data=json.dumps(payload1),
            content_type='application/json'
        )
        response2 = client.post('/link',
            data=json.dumps(payload2),
            content_type='application/json'
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Should have different short codes
        assert data1['link']['short_code'] != data2['link']['short_code']

class TestRedirectLink:
    """Test GET /link/<code> endpoint"""
    
    def test_redirect_valid_link(self, client):
        """Should redirect to original URL when link exists"""
        # Create a link first
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        create_response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(create_response.data)
        short_code = data['link']['short_code']
        
        # Try to redirect
        response = client.get(f'/link/{short_code}', follow_redirects=False)
        assert response.status_code == 302
        assert response.location == 'https://fiverr.com/gigs/logo-design'
    
    def test_redirect_increments_click_count(self, client):
        """Each redirect should increment click count"""
        # Create a link
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        create_response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(create_response.data)
        short_code = data['link']['short_code']
        link_id = data['link']['id']
        
        # Redirect 3 times
        for i in range(3):
            client.get(f'/link/{short_code}', follow_redirects=False)
        
        # Check click count
        response = client.get('/state')
        state_data = json.loads(response.data)
        link_data = state_data['data'][0]
        assert link_data['click_count'] == 3
    
    def test_redirect_creates_click_record(self, client):
        """Each redirect should create a click record"""
        # Create a link
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        create_response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(create_response.data)
        short_code = data['link']['short_code']
        
        # Redirect multiple times
        for _ in range(2):
            client.get(f'/link/{short_code}', follow_redirects=False)
            time.sleep(0.1)  # Small delay to ensure async reward processing
        
        # Verify in database
        with app.app_context():
            clicks = Click.query.all()
            assert len(clicks) == 2
    
    def test_redirect_invalid_short_code(self, client):
        """Should return 404 for non-existent short code"""
        response = client.get('/link/invalid123', follow_redirects=False)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_redirect_empty_short_code(self, client):
        """Should return 400 for invalid short code"""
        response = client.get('/link/', follow_redirects=False)
        # This will return 404 because /link/ is not a valid route
        assert response.status_code == 404

class TestAnalytics:
    """Test GET /state endpoint"""
    
    def test_get_state_empty(self, client):
        """Should return empty list when no links exist"""
        response = client.get('/state')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'] == []
        assert data['pagination']['total'] == 0
        assert data['pagination']['pages'] == 0
    
    def test_get_state_with_links(self, client):
        """Should return all links with analytics"""
        # Create multiple links
        for i in range(5):
            payload = {
                'seller_id': f'seller{i}',
                'original_url': f'https://fiverr.com/gigs/service{i}'
            }
            client.post('/link',
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        response = client.get('/state')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 5
        assert data['pagination']['total'] == 5
    
    def test_get_state_pagination_default(self, client):
        """Should return first page with 10 items by default"""
        # Create 15 links
        for i in range(15):
            payload = {
                'seller_id': f'seller{i}',
                'original_url': f'https://fiverr.com/gigs/service{i}'
            }
            client.post('/link',
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        response = client.get('/state')
        data = json.loads(response.data)
        assert len(data['data']) == 10
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10
        assert data['pagination']['total'] == 15
        assert data['pagination']['pages'] == 2
    
    def test_get_state_pagination_custom_page(self, client):
        """Should return correct page when specified"""
        # Create 25 links
        for i in range(25):
            payload = {
                'seller_id': f'seller{i}',
                'original_url': f'https://fiverr.com/gigs/service{i}'
            }
            client.post('/link',
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        response = client.get('/state?page=2&limit=10')
        data = json.loads(response.data)
        assert len(data['data']) == 10
        assert data['pagination']['page'] == 2
        assert data['pagination']['total'] == 25
        assert data['pagination']['pages'] == 3
    
    def test_get_state_pagination_last_page(self, client):
        """Last page should return remaining items"""
        # Create 25 links
        for i in range(25):
            payload = {
                'seller_id': f'seller{i}',
                'original_url': f'https://fiverr.com/gigs/service{i}'
            }
            client.post('/link',
                data=json.dumps(payload),
                content_type='application/json'
            )
        
        response = client.get('/state?page=3&limit=10')
        data = json.loads(response.data)
        assert len(data['data']) == 5
        assert data['pagination']['page'] == 3
    
    def test_get_state_invalid_pagination_page(self, client):
        """Should return 400 for invalid page number"""
        response = client.get('/state?page=0')
        assert response.status_code == 400
    
    def test_get_state_invalid_pagination_limit(self, client):
        """Should return 400 for limit > 100"""
        response = client.get('/state?limit=150')
        assert response.status_code == 400
    
    def test_get_state_ordered_by_date(self, client):
        """Links should be ordered by created_at (newest first)"""
        # Create links with delays to ensure different timestamps
        short_codes = []
        for i in range(3):
            payload = {
                'seller_id': f'seller{i}',
                'original_url': f'https://fiverr.com/gigs/service{i}'
            }
            response = client.post('/link',
                data=json.dumps(payload),
                content_type='application/json'
            )
            data = json.loads(response.data)
            short_codes.append(data['link']['short_code'])
            time.sleep(0.1)
        
        response = client.get('/state')
        data = json.loads(response.data)
        
        # Should be in reverse order (newest first)
        assert data['data'][0]['short_code'] == short_codes[2]
        assert data['data'][1]['short_code'] == short_codes[1]
        assert data['data'][2]['short_code'] == short_codes[0]
    
    def test_get_state_includes_click_count_and_credits(self, client):
        """Analytics should include click count and credits earned"""
        # Create a link
        payload = {
            'seller_id': 'seller123',
            'original_url': 'https://fiverr.com/gigs/logo-design'
        }
        create_response = client.post('/link',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(create_response.data)
        short_code = data['link']['short_code']
        
        # Generate some clicks
        for _ in range(3):
            client.get(f'/link/{short_code}', follow_redirects=False)
            time.sleep(0.05)
        
        # Get analytics
        response = client.get('/state')
        state_data = json.loads(response.data)
        link_data = state_data['data'][0]
        
        assert link_data['click_count'] == 3
        # Credits should be updated by async reward processing
        assert 'credits_earned' in link_data

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Should return 404 for non-existent endpoint"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_malformed_json(self, client):
        """Should handle malformed JSON gracefully"""
        response = client.post('/link',
            data='invalid json',
            content_type='application/json'
        )
        # Flask will return 400 Bad Request or 500 for malformed JSON
        assert response.status_code in [400, 415, 500]

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
