pipeline {
    agent any
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
        DOCKERHUB_USER = 'jamal1465'
        IMAGE_UNSTABLE = "${DOCKERHUB_USER}/sentiment-api:unstable"
        IMAGE_STABLE = "${DOCKERHUB_USER}/sentiment-api:stable"
        APP_CONTAINER = "sentiment-app-test"
        APP_PORT = "5000"
        KUBECONFIG = "/var/lib/jenkins/.kube/config"
    }
    stages {
        stage('Fetch') {
            steps { checkout scm }
        }
        stage('Build and Run') {
            steps {
                sh '''
                    docker rm -f ${APP_CONTAINER} || true
                    docker build -t ${IMAGE_UNSTABLE} .
                    docker run -d --name ${APP_CONTAINER} --network host ${IMAGE_UNSTABLE}
                    for i in $(seq 1 30); do
                        curl -sf http://localhost:${APP_PORT}/health && echo "App ready!" && break
                        echo "Waiting... ($i/30)"
                        sleep 1
                    done
                '''
            }
        }
        stage('Unit Test') {
            steps {
                sh '''
                    docker run --rm --network host -e BASE_URL=http://localhost:${APP_PORT} \
                    ${IMAGE_UNSTABLE} bash -c "pytest tests/test_api.py -v --tb=short"
                '''
            }
        }
        stage('UI Test') {
            steps {
                sh '''
                    docker run --rm --network host -v $(pwd)/tests:/tests -e APP_URL=http://localhost:${APP_PORT} \
                    --shm-size=2g selenium/standalone-chrome:latest \
                    bash -c "pip install selenium pytest requests -q && pytest tests/test_ui.py -v --tb=short"
                '''
            }
        }
        stage('Build and Push') {
            steps {
                sh '''
                    echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                    docker push ${IMAGE_UNSTABLE}
                    
                    cp app.py /tmp/app-main.py
                    cp requirements.txt /tmp/requirements-main.txt
                    cp Dockerfile /tmp/Dockerfile-main
                    
                    git fetch origin stable-fallback
                    git checkout origin/stable-fallback -- app.py
                    
                    docker build -t ${IMAGE_STABLE} .
                    docker push ${IMAGE_STABLE}
                    
                    cp /tmp/app-main.py app.py
                    cp /tmp/requirements-main.txt requirements.txt
                    cp /tmp/Dockerfile-main Dockerfile
                '''
            }
        }
        stage('Deploy to Minikube') {
            steps {
                sh '''
                    export KUBECONFIG=/var/lib/jenkins/.kube/config
                    kubectl apply -f k8s/
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=300s
                    kubectl rollout status deployment/sentiment-green-deployment --timeout=300s
                    kubectl get svc sentiment-api-service
                '''
            }
        }
    }
    post {
        always {
            sh '''
                docker rm -f ${APP_CONTAINER} || true
                docker logout || true
            '''
        }
    }
}
