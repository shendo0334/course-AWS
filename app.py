import os
import boto3
from flask import Flask, jsonify, request
from botocore.exceptions import ClientError

app = Flask(__name__)

REGION = os.environ.get("AWS_REGION", "ap-south-2")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("abhinand-pipe")

@app.route("/abhinand-cloud/health")
def health():
    return jsonify({"status": "ok", "service": "course-service"}), 200

@app.route("/abhinand-cloud/courses", methods=["POST"])
def add_course():
    try:
        data = request.get_json()

        # Basic validation
        if not data or "id" not in data or "title" not in data:
            return jsonify({"error": "Missing required fields: id, title"}), 400

        course_code = data["id"]

        # Prevent overwrite if course already exists
        courses_table.put_item(
            Item=data,
            ConditionExpression="attribute_not_exists(code)"
        )

        return jsonify({"message": "Course added successfully"}), 201

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return jsonify({"error": "Course already exists"}), 409
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/abhinand-cloud/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    try:
        resp = courses_table.get_item(Key={"id": course_code})
        item = resp.get("Item")
        if not item:
            return jsonify({"error": "Course not found"}), 404
        return jsonify(item), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/abhinand-cloud/courses", methods=["GET"])
def list_courses():
    try:
        resp = courses_table.scan(Limit=50)
        return jsonify(resp.get("Items", [])), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)
    