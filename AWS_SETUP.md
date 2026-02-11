# AWS Setup Instructions for Fiverr Hiring Day

## Quick Setup Steps (Do this when you arrive):

1. **Receive the credentials** from Fiverr (AWS Access Key ID, Secret Access Key, Region, etc.)

2. **Fill in the setup_aws.sh script:**
   Open `setup_aws.sh` and replace:
   - `PROVIDED_KEY` → Your AWS Access Key ID
   - `PROVIDED_SECRET` → Your AWS Secret Access Key
   - `us-east-1` → Region they specify (if different)
   - `anthropic.claude-3-5-sonnet-20240620-v1:0` → Model they specify (if different)

3. **Run the script:**
   ```bash
   source setup_aws.sh
   ```

4. **Verify it worked:**
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_DEFAULT_REGION
   ```

## Using with VS Code Claude Extension:

1. Install the Claude extension (already done ✅)
2. Open VS Code settings (Cmd+, on Mac)
3. Search for "Claude" or "Anthropic"
4. Paste the AWS Bedrock API key they provide
5. The extension will automatically use your AWS environment variables

## Testing the Setup:

```bash
# Test if environment variables are set
echo $AWS_ACCESS_KEY_ID

# Test if Python can access AWS (optional)
python3 -c "import os; print('AWS_ACCESS_KEY_ID:', os.getenv('AWS_ACCESS_KEY_ID'))"
```

## Notes:
- Keep your keys secret - don't commit this script with real credentials to GitHub
- The script is added to .gitignore for safety
- You can run this script fresh each time if needed
