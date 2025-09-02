from flask import Flask, render_template, request, jsonify
from recommendations import generate_recommendation

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    result = generate_recommendation(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
