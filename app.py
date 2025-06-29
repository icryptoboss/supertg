from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def home():
    try:
        # Fetch a random cute dog image
        dog_img_url = requests.get("https://dog.ceo/api/breeds/image/random").json().get("message")
    except:
        # Fallback if API fails
        dog_img_url = "https://images.unsplash.com/photo-1601758123927-196d5fcd53b4"

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cute Dog Viewer</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background-color: #fff;
                font-family: 'Segoe UI', sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }}
            img {{
                max-width: 90%;
                height: auto;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            }}
            h1 {{
                font-size: 1.5em;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>Here's a random cute dog 🐶</h1>
        <img src="{dog_img_url}" alt="Cute Dog">
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
