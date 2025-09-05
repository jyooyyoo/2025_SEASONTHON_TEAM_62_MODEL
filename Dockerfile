# Use the official Python base image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
# The requirements.txt file needs to include gunicorn.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Set the FLASK_APP environment variable.
ENV FLASK_APP=src/app.py

# Expose the port your app runs on. Elastic Beanstalk expects it to be 5000.
EXPOSE 5000

# Run the application using Gunicorn, a production-ready WSGI server.
# Bind to port 5000 for AWS Elastic Beanstalk compatibility.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.app:app"]
```
---
### **의존성 파일 생성**

`Dockerfile`이 `gunicorn`을 설치할 수 있도록 `requirements.txt` 파일을 수정해야 합니다. 터미널에서 아래 명령어를 실행하여 파일을 생성하세요.

```bash
pip freeze > requirements.txt
```
---
### **AWS Elastic Beanstalk으로 배포**

1.  **AWS CLI 설치**: AWS Command Line Interface를 설치하고 구성합니다.
2.  **EB CLI 설치**: Elastic Beanstalk CLI를 설치합니다.
3.  **애플리케이션 생성 및 초기화**: 터미널에서 프로젝트 폴더로 이동하여 다음 명령어를 실행합니다.
    ```bash
    eb init
    ```
    안내에 따라 애플리케이션 이름, 리전(예: `ap-northeast-2` for Seoul) 등을 설정합니다.
4.  **배포**: 다음 명령어를 실행하여 애플리케이션을 배포합니다.
    ```bash
    eb create --platform "64bit Amazon Linux 2 v3.4.7 running Python 3.9" --platform "Docker"

