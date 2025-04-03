# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

.PHONY: help dev prod logs stop rebuild clean deploy terminate

help:
	@echo "🧪 LOCAL DEVELOPMENT COMMANDS:"
	@echo "  make dev              – Start in development mode with hot reload"
	@echo "  make prod             – Start in production mode (detached)"
	@echo "  make logs             – Follow logs from running container"
	@echo "  make stop             – Stop all containers"
	@echo "  make rebuild          – Rebuild image and start fresh"
	@echo "  make clean            – Remove all containers and images"
	@echo ""
	@echo "🚀 DEPLOYMENT TO AWS ELASTIC BEANSTALK:"
	@echo "  make init             – One-time EB app setup (eb init)"
	@echo "  make create           – Create EB environment (after terminate)"
	@echo "  make deploy           – Build, push to ECR, and deploy to EB (enables CloudWatch logs)"
	@echo "  make status           – Show EB environment status and health"
	@echo "  make terminate        – Shut down the EB environment"
	@echo ""
	@echo "🪵 EB LOGGING:"
	@echo "  make logs-eb          – Fetch recent logs from EB"
	@echo "  make logs-eb-full     – Fetch all available EB logs"
	@echo "  make pull-logs        – Download full EB logs to file"
	@echo "  make logs-eb-watch    – Simulate live logs (refresh every 10s)"
	@echo "  make logs-cloudwatch  – True tail logs via CloudWatch (real-time)"

# -- local workflow --

dev:
	docker compose -f $(DEV_COMPOSE) up

prod:
	docker compose up -d

logs:
	docker compose logs -f

stop:
	docker compose -f $(DEV_COMPOSE) down
	docker compose down

rebuild:
	docker compose -f $(DEV_COMPOSE) down
	docker compose down
	docker compose -f $(DEV_COMPOSE) up --build

clean:
	docker compose -f $(DEV_COMPOSE) down --volumes --remove-orphans
	docker compose down --volumes --remove-orphans
	docker image rm $(APP_NAME) || true


# -- AWS workflow --
init:
	eb init -p docker $(APP_NAME) --region $(AWS_REGION)

deploy: build push dockerrun zip upload

build:
	docker build -t $(ECR_REPO):$(IMAGE_TAG) .

push:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URI)
	docker tag $(ECR_REPO):$(IMAGE_TAG) $(ECR_URI):$(IMAGE_TAG)
	docker push $(ECR_URI):$(IMAGE_TAG)

dockerrun:
	@echo "Creating Dockerrun.aws.json..."
	@printf '%s\n' '{' \
	  '  "AWSEBDockerrunVersion": "1",' \
	  '  "Image": {' \
	  '    "Name": "$(ECR_URI):$(IMAGE_TAG)",' \
	  '    "Update": "true"' \
	  '  },' \
	  '  "Ports": [' \
	  '    {' \
	  '      "ContainerPort": 8000' \
	  '    }' \
	  '  ]' \
	  '}' > Dockerrun.aws.json

zip:
	@echo "Zipping Dockerrun.aws.json and .ebextensions..."
	zip -r deploy.zip Dockerrun.aws.json .ebextensions/

upload:
	eb deploy $(ENV_NAME)

terminate:
	eb terminate $(ENV_NAME)

create:
	eb create $(ENV_NAME) --single --instance_type t3.micro

status:
	eb status $(ENV_NAME)


logs-eb:
	@echo "Fetching recent logs from EB environment..."
	eb logs $(ENV_NAME)

logs-eb-full:
	@echo "Fetching all available logs from EB environment..."
	eb logs $(ENV_NAME) --all

pull-logs:
	@echo "Downloading full EB logs to file..."
	eb logs $(ENV_NAME) --all --output file

logs-eb-watch:
	@echo "Simulating live EB logs (refreshing every 10s)..."
	@while true; do \
		clear; \
		echo "🔄 Fetching logs from $(ENV_NAME) at $$(date)"; \
		eb logs $(ENV_NAME); \
		sleep 10; \
	done

logs-cloudwatch:
	@echo "Streaming real-time logs from CloudWatch (Ctrl+C to stop)..."
	aws logs tail "/aws/elasticbeanstalk/$(ENV_NAME)/var/log/web.stdout.log" --follow --region $(AWS_REGION)
