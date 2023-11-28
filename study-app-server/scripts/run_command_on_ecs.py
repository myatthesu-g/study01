#!/usr/bin/env python3.11
###########################################################
# CodeBuild上のpython3は python: 3.11
###########################################################

import argparse
import logging
import os
import sys
import time

import boto3
from botocore.exceptions import ClientError


def stopwatch(func):
    logger = logging.getLogger(__name__)

    def wrapper(*args, **kwargs):
        logger.debug("start function(%s)", func.__name__)
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        logger.info("end function(%s) took %.2f seconds", func.__name__, t2 - t1)
        return result

    return wrapper


def setup_logger(log_level):
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(
        logging.Formatter(
            f"<{os.path.basename(__file__)}> %(name)s [%(levelname)s] %(message)s"
        )
    )
    logger.addHandler(ch)


class RunCommandOnECS:
    LOGGER = logging.getLogger(__name__)

    def __init__(
        self,
        env,
        region,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        profile=None,
    ):
        if aws_access_key_id or aws_secret_access_key:
            session = boto3.session.Session(
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        elif profile:
            session = boto3.session.Session(region_name=region, profile_name=profile)
        else:
            session = boto3.session.Session(region_name=region)

        self.LOGGER.debug(session)
        self.ecs_client = session.client("ecs")
        self.region = region
        self.region_name = self._region_name(region)
        self.env = env
        self.cluster = "study01"
        self.log_client = session.client("logs")
        self._set_parameters(session)

    def _set_parameters(self, session):
        ssm_client = session.client("ssm")
        path = f"/study01/{self.env}/common/aws"
        self.AWS_SUBNET_A = ssm_client.get_parameter(Name=f"{path}/subnet/public_1a")[
            "Parameter"
        ]["Value"]
        self.AWS_SUBNET_C = ssm_client.get_parameter(Name=f"{path}/subnet/public_1c")[
            "Parameter"
        ]["Value"]
        self.AWS_SG_COMMON = ssm_client.get_parameter(
            Name=f"{path}/security_group/common"
        )["Parameter"]["Value"]

        # DB情報
        self.DB_HOST = ssm_client.get_parameter(
            Name=f"/study01/{self.env}/app/db/host"
        )["Parameter"]["Value"]
        self.DB_NAME = ssm_client.get_parameter(
            Name=f"/study01/{self.env}/app/db/name"
        )["Parameter"]["Value"]
        self.DB_USER = ssm_client.get_parameter(
            Name=f"/study01/{self.env}/app/db/username"
        )["Parameter"]["Value"]
        self.DB_PASSWORD = ssm_client.get_parameter(
            Name=f"/study01/{self.env}/app/db/password"
        )["Parameter"]["Value"]

        self.LOGGER.debug(
            "set parameters: %s, %s, %s",
            self.AWS_SUBNET_A,
            self.AWS_SUBNET_C,
            self.AWS_SG_COMMON,
        )

    @staticmethod
    def _region_name(region_id):
        if region_id == "ap-northeast-1":
            return "tokyo"
        elif region_id == "us-west-2":
            return "oregon"
        elif region_id == "us-east-1":
            return "virginia"
        else:
            raise ValueError(f"unknown region: {region_id}")

    @staticmethod
    def _task_role_env_name(env):
        if env.startswith("demo"):
            return "demo"
        elif env.startswith("qa"):
            return "qa"
        else:
            return env

    @stopwatch
    def _register_task(self, command, image_tag, container_size, env_var_dict):
        additional_env_vars = [{"name": k, "value": v} for k, v in env_var_dict.items()]
        cpu, memory = self._resource_combination(container_size)
        task_role_env_name = self._task_role_env_name(self.env)
        task_def = self.ecs_client.register_task_definition(
            family=f"{self.env}_study01_run_command",
            taskRoleArn=f"arn:aws:iam::XXXXXXXXX:role/study01-{task_role_env_name}-ECSServiceTask-{self.region_name}-role",
            executionRoleArn="arn:aws:iam::XXXXXXXXX:role/ecsTaskExecutionRole",
            networkMode="awsvpc",
            containerDefinitions=[
                {
                    "name": "study01-fastapi",
                    "image": f"XXXXXXXXX.dkr.ecr.{self.region}.amazonaws.com/study01-fastapi-{self.env}:{image_tag}",
                    "essential": True,
                    "command": command,
                    "environment": [
                        {"name": "APPLICATION_ENV", "value": self.env},
                        {"name": "APPLICATION_ROLE", "value": "run_command"},
                        {"name": "DB_HOST", "value": self.DB_HOST},
                        {"name": "DB_NAME", "value": self.DB_NAME},
                        {"name": "DB_USER", "value": self.DB_USER},
                        {"name": "DB_PASSWORD", "value": self.DB_PASSWORD},
                    ]
                    + additional_env_vars,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": self._log_group(),
                            "awslogs-region": self.region,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                },
            ],
            requiresCompatibilities=["FARGATE"],
            cpu=cpu,
            memory=memory,
            tags=[
                {"key": "Name", "value": "run_command"},
                {"key": "Product", "value": "study01"},
                {"key": "Env", "value": self.env},
            ],
        )
        self.LOGGER.debug(task_def)
        self.LOGGER.info(
            "task definition(%s) registered",
            task_def["taskDefinition"]["taskDefinitionArn"],
        )
        return task_def

    @stopwatch
    def _run_task(self, task):
        running_task = self.ecs_client.run_task(
            cluster=self.cluster,
            taskDefinition=task["taskDefinition"]["taskDefinitionArn"],
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": ["subnet-XXXXXXXXX", "subnet-XXXXXXXXX"],
                    "securityGroups": ["sg-XXXXXXXXX"],
                    "assignPublicIp": "ENABLED",
                }
            },
            tags=[
                {"key": "Name", "value": "run_command"},
                {"key": "Product", "value": "study01"},
                {"key": "Env", "value": self.env},
            ],
        )
        self.LOGGER.debug(running_task)
        self.LOGGER.info("task(%s) started", running_task["tasks"][0]["taskArn"])
        return running_task

    @stopwatch
    def _wait_task(self, running_task):
        task_arn = running_task["tasks"][0]["taskArn"]
        waiter = self.ecs_client.get_waiter("tasks_stopped")
        self.LOGGER.info("waiting for task(%s) to finish...", task_arn)
        waiter.wait(
            cluster=self.cluster,
            tasks=[
                task_arn,
            ],
            WaiterConfig={"Delay": 10, "MaxAttempts": 100},
        )
        self.LOGGER.info("task(%s) ended", task_arn)

        stopped_task = self.ecs_client.describe_tasks(
            cluster=self.cluster,
            tasks=[
                task_arn,
            ],
        )
        self.LOGGER.debug(stopped_task)
        task = stopped_task["tasks"][0]
        container = task["containers"][0]
        if self._exit_code(stopped_task) == 0:
            self.LOGGER.info("task(%s) completed. ALL GREEN!", task["taskArn"])
        else:
            self.LOGGER.error(
                "task(%s) failed. exit code: %s, reason: task(%s), container(%s)",
                task["taskArn"],
                container.get("exitCode"),
                task["stoppedReason"],
                container.get("reason"),
            )
        return stopped_task

    @stopwatch
    def _print_log(self, stopped_task):
        task_arn = stopped_task["tasks"][0]["taskArn"]
        group = self._log_group()
        stream = self._log_stream(task_arn)
        try:
            self.LOGGER.info("getting task(%s) log events...", task_arn)
            log_events = self.log_client.get_log_events(
                logGroupName=group, logStreamName=stream, startFromHead=True
            )
            self.LOGGER.debug(log_events)
            for event in log_events["events"]:
                self.LOGGER.info(event["message"])

            if log_events["nextForwardToken"]:
                self._print_log_r(group, stream, log_events["nextForwardToken"])

            self.LOGGER.info("end of task(%s) log events", task_arn)
        except ClientError as error:
            self.LOGGER.error(
                "failed to get log events from group: %s, stream: %s", group, stream
            )
            self.LOGGER.error(error)

    def _resource_combination(self, container_size):
        if container_size == "small":
            return "256", "512"
        elif container_size == "medium":
            return "512", "2048"
        elif container_size == "large":
            return "1024", "8192"
        elif container_size == "huge":
            return "2048", "32768"
        else:
            raise f"Unknown size: {container_size}"

    def _print_log_r(self, group, stream, next_token):
        log_events = self.log_client.get_log_events(
            logGroupName=group,
            logStreamName=stream,
            nextToken=next_token,
            startFromHead=True,
        )
        self.LOGGER.debug(log_events)
        for event in log_events["events"]:
            self.LOGGER.info(event["message"])

        if (
            log_events["nextForwardToken"] is None
            or log_events["nextForwardToken"] == next_token
        ):
            return
        else:
            self._print_log_r(group, stream, log_events["nextForwardToken"])

    def _log_group(self):
        return f"/study01/{self.env}/ecs/stud01_run_command"

    def _log_stream(self, task_arn):
        task_id = task_arn.split("/")[2]
        return f"ecs/study01-fastapi/{task_id}"

    @staticmethod
    def _parse_env_vars(env_vars):
        if env_vars is None:
            return {}
        return {e[0]: e[1] for e in [env_var.split("=") for env_var in env_vars]}

    @staticmethod
    def _exit_code(stopped_task):
        task = stopped_task["tasks"][0]
        container = task["containers"][0]
        exit_code = container.get("exitCode")
        if isinstance(exit_code, int):
            return exit_code
        else:
            return 1

    @staticmethod
    @stopwatch
    def main(
        command,
        image_tag,
        env,
        container_size,
        env_vars,
        region,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        profile=None,
    ):
        if len(command) == 0:
            raise ArgumentError("argument 'command...' is required.")
        try:
            env_var_dict = RunCommandOnECS._parse_env_vars(env_vars)
        except Exception as e:
            raise ArgumentError("option '--env-var' expected form is NAME=VAR.")

        self = RunCommandOnECS(
            env, region, aws_access_key_id, aws_secret_access_key, profile
        )
        task_def = self._register_task(command, image_tag, container_size, env_var_dict)
        running_task = self._run_task(task_def)
        stopped_task = self._wait_task(running_task)
        self._print_log(stopped_task)
        return self._exit_code(stopped_task)


class ArgumentError(Exception):
    def __init__(self, message):
        self.message = message


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="run command on ECS using amidala container."
    )
    parser.add_argument(
        "--image-tag", type=str, default="latest", help="container image tag [latest]"
    )
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        choices=[
            "dev",
            "prod",
        ],
        help="environment [dev]",
    )
    parser.add_argument(
        "--container-size",
        type=str,
        default="small",
        choices=["small", "medium", "large", "huge"],
    )
    parser.add_argument(
        "--env-var",
        type=str,
        metavar="NAME=VALUE",
        action="append",
        help="environment variable",
    )
    parser.add_argument(
        "--aws-region",
        type=str,
        default="ap-northeast-1",
        help="AWS region [ap-northeast-1]",
    )
    parser.add_argument(
        "--aws-access-key-id",
        type=str,
        help="AWS access key id [your default credential]",
    )
    parser.add_argument(
        "--aws-secret-access-key",
        type=str,
        help="AWS secret access key [your default credential]",
    )
    parser.add_argument(
        "--aws-profile", type=str, help="AWS profile name [your default profile]"
    )
    parser.add_argument("--verbose", action="store_true", help="verbose mode")
    parser.add_argument(
        "command",
        type=str,
        nargs=argparse.REMAINDER,
        help="command run on ECS. required. *place this arguments last*",
    )
    parsed_args = parser.parse_args()

    setup_logger(logging.DEBUG if parsed_args.verbose else logging.INFO)
    try:
        exit_code = RunCommandOnECS.main(
            parsed_args.command,
            parsed_args.image_tag,
            parsed_args.env,
            container_size=parsed_args.container_size,
            env_vars=parsed_args.env_var,
            region=parsed_args.aws_region,
            aws_access_key_id=parsed_args.aws_access_key_id,
            aws_secret_access_key=parsed_args.aws_secret_access_key,
            profile=parsed_args.aws_profile,
        )
        if exit_code != 0:
            logging.getLogger(__name__).error("task exit with code(%s)", exit_code)
            sys.exit(exit_code)
    except ArgumentError as e:
        parser.print_help()
        parser.error(e.message)
