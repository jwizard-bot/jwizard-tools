from argparse import ArgumentParser
from logging import error, info

from dotenv import load_dotenv

from common.header import print_header
from common.logger import init_logger
from remote_invoker.project_remote_call import (
  ApiProjectRemoteCall,
  CoreProjectRemoteCall,
  DashboardPageProjectRemoteCall,
  LandingPageProjectRemoteCall,
  ManagementProjectRemoteCall,
)

init_logger()
load_dotenv()


def main():
  print_header(initiator=__file__)

  arg_parser = ArgumentParser()
  arg_parser.add_argument("--name", type=str, required=True)
  arg_parser.add_argument("--inputDir", type=str, required=True)
  args = arg_parser.parse_args()

  project_remote_call = None

  try:
    projects_remote_call = {
      "api": ApiProjectRemoteCall,
      "core": CoreProjectRemoteCall,
      "dashboard": DashboardPageProjectRemoteCall,
      "landing-page": LandingPageProjectRemoteCall,
      "management": ManagementProjectRemoteCall,
    }
    project_remote_call = projects_remote_call.get(args.name, None)(input_path=args.inputDir)
    project_remote_call.perform_call()

  except Exception as ex:
    error(f"Unable to execute action. Cause: \"{ex}\".")
    exit(1)

  finally:
    if project_remote_call:
      project_remote_call.revoke_access()

  info("Finished.")


if __name__ == "__main__":
  main()
