import streamlit.components.v1 as components
import html

# Custom Copy to Clipboard Function
def copy_to_clipboard(text):
    safe_text = html.escape(text).replace("\n", "\\n")
    components.html(
        f"""
        <html>
          <head>
            <style>
              .copy-button {{
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
              }}
            </style>
            <script>
              function copyText() {{
                navigator.clipboard.writeText("{safe_text}")
                  .then(function() {{
                    alert("Copied to clipboard!");
                  }})
                  .catch(function(err) {{
                    alert("Copy failed: " + err);
                  }});
              }}
            </script>
          </head>
          <body>
            <button class="copy-button" onclick="copyText()">Copy to Clipboard</button>
          </body>
        </html>
        """,
        height=50,
        scrolling=False,
    )