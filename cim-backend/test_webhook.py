import requests
import os

# The local URL of your running application
WEBHOOK_URL = "http://127.0.0.1:8000/ingest/webhook"

# The path to your dummy CIM file
# Make sure you have a file named 'test-cim.pdf' in the same directory
FILE_PATH = "test-cim.pdf"

def send_test_request():
    """
    Simulates a Mailgun request with one attachment to the local server.
    """
    if not os.path.exists(FILE_PATH):
        print(f"Error: Test file not found at '{FILE_PATH}'")
        # Create a dummy file if it doesn't exist
        with open(FILE_PATH, "wb") as f:
            f.write(b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000112 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF")
        print(f"Created a dummy file at '{FILE_PATH}' for testing.")


    # Form data that mimics Mailgun's fields
    payload = {
        'sender': 'script-test@example.com',
        'recipient': 'deals@yourdomain.com',
        'subject': 'Python Script Test',
        'body-plain': 'Testing the webhook from a Python script. I am a CIM',
        'attachment-count': '1'
    }

    # The file to be uploaded
    files = {
        'attachment-1': (os.path.basename(FILE_PATH), open(FILE_PATH, 'rb'), 'application/pdf')
    }

    print(f"Sending POST request to {WEBHOOK_URL}...")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, files=files)
        
        # Print the server's response
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(response.json())

    except requests.exceptions.ConnectionError as e:
        print("\nConnection Error: Is your uvicorn server running?")
        print(e)


if __name__ == "__main__":
    send_test_request()