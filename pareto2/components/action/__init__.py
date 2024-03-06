from pareto.aws.lambda import Function as FunctionBase

class Function(FunctionBase):
    
    def __init__(self, action):
        code = {
            "S3Bucket": {"Ref": "artifacts-bucket"},
            "S3Key": {"Ref": "artifacts-key"}
        }
        envvars = action["env"]["variables"] if "env" in action else {}
        layers = [f"{pkgname}-layer-arn" for pkgname in action.get("layers", [])]
        handler = f"{action['path'].replace('-', '/')}/index.handler"
        super().__init__(action["name"],
                         "function-role",
                         code,
                         size=action["size"],
                         timeout=action["timeout"],
                         envvars=envvars,
                         layers=layers,
                         handler=handler)
