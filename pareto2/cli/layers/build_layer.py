from botocore.exceptions import ClientError

import boto3, time

Pip, Git = "pip", "git"

PythonRuntime="3.8"

def build_layer(cb, config, pkg,
                wait=3,
                maxtries=100,
                exitcodes=["SUCCEEDED",
                           "FAILED",
                           "STOPPED"]):
    def pip_target(pkg):
        if pkg["type"]==Pip:
            target=pkg["name"]
            if "version" in pkg:
                target+="==%s" % pkg["version"]
            return target
        elif pkg["type"]==Git:
            target="git+https://github.com/%s/%s" % (pkg["owner"],
                                                     pkg["name"])
            if "version" in pkg:                
                target+="@%s" % pkg["version"]
            return target
        else:
            raise RuntimeError("type not supported")
    def init_env(pkg, runtime=PythonRuntime):
        target=pip_target(pkg)
        print ("target: %s" % target)
        if "version" in pkg:
            s3key="layer-%s-%s.zip" % (pkg["name"],
                                       pkg["version"].replace(".", "-"))
        else:
            s3key="layer-%s.zip" % pkg["name"]
        print ("s3 key: %s" % s3key)
        return [{"name": k,
                 "value": v,
                 "type": "PLAINTEXT"}
                for k, v in [("PIP_TARGET", target),
                             ("S3_KEY", s3key),
                             ("PYTHON_RUNTIME", runtime)]]
    def get_build(cb, projectname, buildid):
        resp=cb.list_builds_for_project(projectName=projectname)
        if ("ids" not in resp or
            resp["ids"]==[]):
            raise RuntimeError("no build ids found")
        builds={build["id"]:build
                for build in cb.batch_get_builds(ids=resp["ids"])["builds"]}
        if buildid not in builds:
            raise RuntimeError("build id not found")
        return builds[buildid]    
    projectname="%s-layers" % config["AppName"]
    env=init_env(pkg)
    buildid=cb.start_build(projectName=projectname,
                           environmentVariablesOverride=env)["build"]["id"]
    print ("build id: %s" % buildid)
    print ()                                                                      
    for i in range(maxtries):
        time.sleep(wait)
        build=get_build(cb, projectname, buildid)
        print ("%i/%i\t%s\t%s" % (1+i,
                                 maxtries,
                                 build["currentPhase"],
                                 build["buildStatus"]))
        if build["buildStatus"] in exitcodes:
            break
        
if __name__=="__main__":
    try:

        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter type, name")
        pkgtype, pkgname = sys.argv[1:3]
        if pkgtype not in [Pip, Git]:
            raise RuntimeError("pkg type not supported")
        from pareto2.cli import load_config
        config=load_config()
        layer={"type": pkgtype,
               "name": pkgname}
        if pkgtype==Pip and len(sys.argv) >= 4:
            layer["version"]=sys.argv[3]
        elif pkgtype==Git:
            if len(sys.argv) < 4:
                raise RuntimeError("please enter (repo) owner")
            layer["owner"]=sys.argv[3]
            if len(sys.argv) >= 5:
                layer["version"]=sys.argv[4]
        cb=boto3.client("codebuild")
        build_layer(cb, config, layer)
    except ClientError as error:
        print ("Error: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

