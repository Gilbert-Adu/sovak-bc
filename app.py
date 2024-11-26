from flask import Flask, jsonify, request, redirect # type: ignore
from flask_cors import CORS # type: ignore
import base64
import boto3 # type: ignore
from io import BytesIO
from functions import upload_file_to_s3, generate_file_name, insert_into_db, get_all_posts, get_post_by_id, insert_comment, get_comments_by_id
import stripe # type: ignore
from datetime import datetime
import asyncio
from dotenv import load_dotenv # type: ignore
import os


app = Flask(__name__)
CORS(app, origins="*")

load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region_name = os.getenv("REGION_NAME")

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name  
)

@app.route('/')
def home():
    all_posts = get_all_posts()
    #sorted_posts = sorted(all_posts, key=lambda x: datetime.strptime(x['date_submitted'], '%Y-%m-%d'), reverse=True)
    return jsonify(all_posts)

#stripe 
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

#s3 bucket
bucket_name =  os.getenv("S3_BUCKET_NAME")

@app.route('/test', methods=['GET'])
def test_route():

    return jsonify({"message": "successfully working!"})

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_name =  generate_file_name()

    try:
        s3_client.upload_fileobj(
            file, 
            bucket_name,
            file_name,
            ExtraArgs={'ContentType': file.content_type}
        )
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"

        return jsonify({"fileUrl": file_url}), 200
        
    except Exception as e:
        return jsonify({"error": "failed to upload the file"}), 500


#returns details specific to a post
@app.route('/post-details', methods=['GET'])
def post_details():
    post_id = request.args.get('post_id')
    response = get_post_by_id(post_id)
    return jsonify(response)

#returns comments specific to a post
@app.route('/get-comments', methods=['GET'])
def get_post_comments():
    post_id = request.args.get('post_id')
    response = get_comments_by_id(post_id)
    return jsonify(response)
    
#creates a comment
@app.route('/create-comment', methods=['POST'])
def create_comment():
    data = request.json
    try:
        post_id = data.get("post_id")
        comment_body = data.get("comment_body")
        author = data.get("author")

        insert_comment(post_id, author, comment_body)
        print("created comment successfully!!!")
    
    except Exception as e:
        print("could not get comment info from form in frontend: ", str(e))

    return jsonify({"message": "success"})

#http://34.201.173.137:3000/
@app.route('/create-report', methods=['POST'])
def create_report():
    data = request.json
    #reporter_name = data.get("reporter_name")
    userData = data.get("userData")
    item_data = {
        "reporter_name": userData["reporter_name"],
        "reporter_street_address": userData["reporter_street_address"],
        "reporter_city": userData["reporter_city"],
        "reporter_state": userData["reporter_state"],
        "reporter_zipcode": userData["reporter_zipcode"],
        "reporter_country": userData["reporter_country"],
        "videoUpload": userData["videoUpload"],
        "reporter_phone": userData["reporter_phone"],
        "subject_name": userData["subject_name"],
        "subject_address": userData["subject_address"],
        "subject_city": userData["subject_city"],
        "subject_state": userData["subject_state"],
        "subject_zip": userData["subject_zip"],
        "subject_country": userData["subject_country"],
        "subject_phone": userData["subject_phone"],
        "incident_type": userData["incident_type"],
        "incident_details": userData["incident_details"],
        "incident_date": userData["incident_date"],
        "incident_address": userData["incident_address"],
        "incident_city": userData["incident_city"],
        "incident_state": userData["incident_state"],
        "incident_zip": userData["incident_zip"],
        "incident_country": userData["incident_country"],
        "report_type": userData["report_type"],
        "date_submitted": userData["today_date"],
        "address_question": userData["address_question"],
        "photo_id": data.get("photoID"),
        "votes": "0"

    }

    if userData["altReport"] == 'yes':
            item_data["third_party"] = userData["altReport"]
            item_data["third_party_reporter"] = userData["alt_reporter_name"]

    else:
        item_data["third_party"] = userData["altReport"]
        item_data["third_party_reporter"] = "none"


    
    try:
        

        if data.get("userData")['videoUpload'] == "yes":
            item_data['video_url'] = data.get("videoUrl")
            #print("data: ", data)
            insert_into_db(item_data)

                
            
        else:
            item_data['video_url'] = "none"
            insert_into_db(item_data)
        #print("userData: ", userData)

    except Exception as e:
        print("This error occurred: ", e)

    return jsonify({"message": "successfully saved post"})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)