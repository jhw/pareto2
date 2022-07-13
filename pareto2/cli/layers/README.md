```
(env) jhw@Justins-Air wol_trading_2122 % ./scripts/layers/list_projects.sh 
-------------------------
|     ListProjects      |
+-----------------------+
||      projects       ||
|+---------------------+|
||  radio-woldo-layer  ||
|+---------------------+|
(env) jhw@Justins-Air wol_trading_2122 % python scripts/layers/create_project.py 
creating role
waiting for policy creation ..
waiting for role creation ..
trying to create project [1/20]
trying to create project [2/20]
trying to create project [3/20]
trying to create project [4/20]
project created :)
(env) jhw@Justins-Air wol_trading_2122 % python scripts/layers/build_layer.py pip numpy
target: numpy
s3 key: layer-numpy.zip
build id: wol-trading-layers:53c15d1b-bf77-46a3-a03a-92201f513a3d

1/100	PROVISIONING	IN_PROGRESS
2/100	PROVISIONING	IN_PROGRESS
3/100	PROVISIONING	IN_PROGRESS
4/100	PROVISIONING	IN_PROGRESS
5/100	PROVISIONING	IN_PROGRESS
6/100	PROVISIONING	IN_PROGRESS
7/100	INSTALL	IN_PROGRESS
8/100	INSTALL	IN_PROGRESS
9/100	INSTALL	IN_PROGRESS
10/100	INSTALL	IN_PROGRESS
11/100	UPLOAD_ARTIFACTS	IN_PROGRESS
12/100	FINALIZING	IN_PROGRESS
13/100	COMPLETED	SUCCEEDED
(env) jhw@Justins-Air wol_trading_2122 % python scripts/layers/build_layer.py git readability jhw "1.0.4"
target: git+https://github.com/jhw/readability@1.0.4
s3 key: layer-readability-1-0-4.zip
build id: wol-trading-layers:6cd8d062-507e-4ec2-8062-faa70683080c

1/100	PROVISIONING	IN_PROGRESS
2/100	PROVISIONING	IN_PROGRESS
3/100	PROVISIONING	IN_PROGRESS
4/100	PROVISIONING	IN_PROGRESS
5/100	PROVISIONING	IN_PROGRESS
6/100	PROVISIONING	IN_PROGRESS
7/100	INSTALL	IN_PROGRESS
8/100	INSTALL	IN_PROGRESS
9/100	INSTALL	IN_PROGRESS
10/100	INSTALL	IN_PROGRESS
11/100	INSTALL	IN_PROGRESS
12/100	FINALIZING	IN_PROGRESS
13/100	COMPLETED	SUCCEEDED
(env) jhw@Justins-Air wol_trading_2122 % python scripts/layers/list_artifacts.py 
18883399	layer-numpy.zip
8539881	layer-readability-1-0-4.zip
(env) jhw@Justins-Air wol_trading_2122 % ./scripts/layers/list_projects.sh 
--------------------------
|      ListProjects      |
+------------------------+
||       projects       ||
|+----------------------+|
||  wol-trading-layers  ||
||  radio-woldo-layer   ||
|+----------------------+|
(env) jhw@Justins-Air wol_trading_2122 % ./scripts/layers/delete_project.sh 
(env) jhw@Justins-Air wol_trading_2122 % ./scripts/layers/list_projects.sh 
-------------------------
|     ListProjects      |
+-----------------------+
||      projects       ||
|+---------------------+|
||  radio-woldo-layer  ||
|+---------------------+|
```