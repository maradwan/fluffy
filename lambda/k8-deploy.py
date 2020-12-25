import json
import base64
import boto3
import re
from botocore.signers import RequestSigner
from kubernetes import client, config
from os import environ as env

APP_NAME = env.get("APP_NAME")
APP_BASE_IMAGE = env.get("APP_BASE_IMAGE")
DEPLOYMENT_NAME = env.get("DEPLOYMENT_NAME")
REGION_NAME = env.get("REGION_NAME")
EKS_CLUSTER_NAME = env.get("EKS_CLUSTER_NAME")
EKS_CLUSTER_API = env.get("EKS_CLUSTER_API")

code_pipeline = boto3.client('codepipeline', region_name=REGION_NAME)
ssm = boto3.client('ssm', region_name=REGION_NAME)

def get_bearer_token(cluster_id, region):
    STS_TOKEN_EXPIRES_IN = 60
    access_key = ssm.get_parameter(Name='/fluffy/k8/aws_access_key')
    aws_access_key = access_key['Parameter']['Value']
    secret_key = ssm.get_parameter(Name='/fluffy/k8/aws_secret_access_key', WithDecryption=True)
    aws_secret_key= secret_key['Parameter']['Value']

    session = boto3.session.Session(aws_access_key_id= aws_access_key, aws_secret_access_key=aws_secret_key,region_name=REGION_NAME)
    client = session.client('sts', region_name=region)
    service_id = client.meta.service_model.service_id

    signer = RequestSigner(
        service_id,
        region,
        'sts',
        'v4',
        session.get_credentials(),
        session.events
    )

    params = {
        'method': 'GET',
        'url': 'https://sts.{}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'.format(region),
        'body': {},
        'headers': {
            'x-k8s-aws-id': cluster_id
        },
        'context': {}
    }

    signed_url = signer.generate_presigned_url(
        params,
        region_name=region,
        expires_in=STS_TOKEN_EXPIRES_IN,
        operation_name=''
    )

    base64_url = base64.urlsafe_b64encode(signed_url.encode('utf-8')).decode('utf-8')

    # remove any base64 encoding padding:
    return 'k8s-aws-v1.' + re.sub(r'=*', '', base64_url)

# If making a HTTP request you would create the authorization headers as follows:

#headers = {'Authorization': 'Bearer ' + get_bearer_token('testing', 'eu-west-1')}

def create_deployment_object():
    # Configureate Pod template container
    container = client.V1Container(
        name = APP_NAME,
        image= APP_BASE_IMAGE,
        ports=[client.V1ContainerPort(container_port=80)],
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": "200Mi"},
            limits={"cpu": "500m", "memory": "500Mi"}
        )
    )
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": APP_NAME}),
        spec=client.V1PodSpec(containers=[container]))
    # Create the specification of deployment
    spec = client.V1DeploymentSpec(
        replicas=3,
        template=template,
        selector={'matchLabels': {'app': APP_NAME}})
    # Instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=DEPLOYMENT_NAME),
        spec=spec)

    return deployment


def create_deployment(api_instance, deployment):
    # Create deployement
    api_response = api_instance.create_namespaced_deployment(
        body=deployment,
        namespace="default")
    print("Deployment created. status='%s'" % str(api_response.status))


def update_deployment(api_instance, deployment, docker_image):
    # Update container image
    deployment.spec.template.spec.containers[0].image = docker_image
    # Update the deployment
    api_response = api_instance.patch_namespaced_deployment(
        name=DEPLOYMENT_NAME,
        namespace="default",
        body=deployment)
    print("Deployment updated. status='%s'" % str(api_response.status))


def delete_deployment(api_instance):
    # Delete deployment
    api_response = api_instance.delete_namespaced_deployment(
        name=DEPLOYMENT_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5))
    print("Deployment deleted. status='%s'" % str(api_response.status))


def put_job_success(job, message):
    """Notify CodePipeline of a successful job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_success_result()

    """
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)

def put_job_failure(job, message):
    """Notify CodePipeline of a failed job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_failure_result()

    """
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job, failureDetails={'message': message, 'type': 'JobFailed'})


def lambda_handler(event, context):
    # TODO implement
    print('event')
    print(event)
    headers = {'Authorization': 'Bearer ' + get_bearer_token(EKS_CLUSTER_NAME, REGION_NAME)}
    token=headers['Authorization'].split()[1]

    api_token = token
    configuration = client.Configuration()
    configuration.host = EKS_CLUSTER_API
    configuration.verify_ssl = False
    configuration.debug = True
    configuration.api_key['authorization'] = "Bearer " + api_token
    configuration.assert_hostname = True
    configuration.verify_ssl = False
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)
    #print (ret)

    apps_v1 = client.AppsV1Api()

    job_id = event['CodePipeline.job']['id']

    try:
        deployment = create_deployment_object()

        ###create_deployment(apps_v1, deployment)

        # Roll Back Previous Version
        if event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters'] == '{"rollback": "True", "version":-2}':
            response = ssm.get_parameter_history(Name='/fluffy/prod/docker-image',WithDecryption=False)
            docker_image = response['Parameters'][-2]['Value']

        elif event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters'] == '{"rollout": "True"}':
            response = ssm.get_parameter(Name='/fluffy/prod/docker-image', WithDecryption=False)
            docker_image= response['Parameter']['Value']

        update_deployment(apps_v1, deployment, docker_image)

        put_job_success(job_id, 'Job Successed')

    except:
        put_job_failure(job_id, 'Job Failed')

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }