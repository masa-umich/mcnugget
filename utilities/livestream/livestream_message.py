from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Hard-coded list of pre-programmed states
PRE_PROGRAMMED_STATES = [
    "ASSEMBLING SYSTEM 1/10",
    "LEAK CHECKS 2/10",
    "RAISING ROCKET 3/10",
    "FILLING FUEL 4/10",
    "FILLING PRESSURANT 5/10",
    "FILLING OXIDIZER 6/10",
    "DISCONNECTING QDS 7/10",
    "GO/NO-GO POLL 8/10",
    "AUTOSEQUENCE START 9/10",
    "LAUNCH 10/10",
    "ABORT"
]

# Active state of the overlay
system_state = {
    "routine_state": PRE_PROGRAMMED_STATES[0],
    "custom_message": "RANGE IS RED",
    "show_custom": False
}

# The HTML for the web portal
PORTAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MASA Stream Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
            background-color: #eeeeea; /* MASA Sand */
            color: #00274c; /* MASA Blue */
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: white;
            padding: 30px 40px;
            border-radius: 8px;
            box-shadow: 0 10px 20px rgba(0,39,76,0.1);
            border-top: 8px solid #ffcb05; /* MASA Maize */
            width: 90%;
            max-width: 550px;
        }
        h1 { font-weight: 900; text-align: center; margin-top: 0; margin-bottom: 5px; }
        p.subtitle { text-align: center; margin-top: 0; margin-bottom: 30px; font-weight: 600;}
        
        label { font-weight: 700; display: block; margin-bottom: 8px; font-size: 14px; text-transform: uppercase;}
        
        select, input[type="text"] {
            width: 100%;
            padding: 12px;
            box-sizing: border-box;
            border: 2px solid #00274c;
            border-radius: 4px;
            font-family: 'Montserrat', sans-serif;
            font-size: 16px;
            margin-bottom: 25px;
            font-weight: 700;
        }
        
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #ef4624;
        }
        .toggle-container input[type="checkbox"] {
            width: 20px; height: 20px; cursor: pointer;
        }
        .toggle-container label { margin: 0; cursor: pointer; }

        button {
            background-color: #ef4624; /* MASA Vermillion */
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: 700;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-family: 'Montserrat', sans-serif;
            text-transform: uppercase;
            margin-top: 10px;
        }
        button:hover { background-color: #d13a1b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MASA Limelight</h1>
        <p class="subtitle">Broadcast Director Portal</p>
        
        <form action="/update" method="POST">
            
            <label>1. Routine Flight State</label>
            <select name="routine_state">
                {% for state in states %}
                    <option value="{{ state }}" {% if state == current_routine %}selected{% endif %}>{{ state }}</option>
                {% endfor %}
            </select>

            <label>2. Custom Alert Message</label>
            <input type="text" name="custom_message" placeholder="E.G. HOLD FOR WIND..." value="{{ current_custom }}" maxlength="40" autocomplete="off">
            
            <div class="toggle-container">
                <input type="checkbox" id="show_custom" name="show_custom" value="yes" {% if show_custom %}checked{% endif %}>
                <label for="show_custom">Display Custom Alert Box on Stream</label>
            </div>

            <button type="submit">Push to Stream</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(PORTAL_HTML, 
                                  states=PRE_PROGRAMMED_STATES,
                                  current_routine=system_state['routine_state'],
                                  current_custom=system_state['custom_message'],
                                  show_custom=system_state['show_custom'])

@app.route('/update', methods=['POST'])
def update():
    system_state['routine_state'] = request.form.get('routine_state')
    custom_msg = request.form.get('custom_message')
    
    if custom_msg:
        system_state['custom_message'] = custom_msg.upper()
        
    system_state['show_custom'] = 'show_custom' in request.form
    return index()

@app.route('/api/state')
def get_state():
    return jsonify(system_state)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)