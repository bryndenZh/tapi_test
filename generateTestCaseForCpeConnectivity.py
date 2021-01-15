import mysql.connector
import json
import uuid

tapi_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="cpe_b",
    auth_plugin='mysql_native_password'
)
resource_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="cpe_resource"
)
topology_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="cpe_topology"
)
tapi = tapi_db.cursor(buffered=True)
topology = topology_db.cursor(buffered=True)
resource = resource_db.cursor(buffered=True)

f = open("config.json")
config = json.load(f)

r_file = open("template.json")
request = json.load(r_file)
r_file.close()

src_topology_node_id = config["src_topology_node_id"]
dst_topology_node_id = config["dst_topology_node_id"]

# 查找对应的 resource me id
tapi.execute("select resource_me_id from node_relation where topology_node_id= %s", (src_topology_node_id,))
src_resource_me_id = tapi.fetchone()[0]
tapi.execute("select resource_me_id from node_relation where topology_node_id = %s", (dst_topology_node_id,))
dst_resource_me_id = tapi.fetchone()[0]
print("resource me id", src_resource_me_id, dst_resource_me_id)

# # 在 topology.link 中查找链路
# topology.execute("select a_ptp_id, z_ptp_id from link where a_node_id = %s and z_node_id = %s ", (src_topology_node_id, dst_topology_node_id))
# src_nni_ptp, dst_nni_ptp = topology.fetchone()
# print(src_nni_ptp, " ", dst_nni_ptp)

# 选择两个网元上的 uni ptp
src_uni_loc = config["src_uni_loc"]
dst_uni_loc = config["dst_uni_loc"]
resource.execute("select id from ptp where interface_type = 'UNI' and me_id = %s", (src_resource_me_id,))
src_uni_ptp = resource.fetchall()[src_uni_loc][0]
resource.execute("select id from ptp where interface_type = 'UNI' and me_id = %s", (dst_resource_me_id,))
dst_uni_ptp = resource.fetchall()[dst_uni_loc][0]
print("uni_ptp_id", src_uni_ptp, dst_uni_ptp)

# 查找 uni ptp 对应的 nep
tapi.execute("select tapi_node_edge_point_uuid from node_edge_point_relation where resource_ptp_id = %s",
             (src_uni_ptp,))
src_uni_nep = tapi.fetchone()[0]
tapi.execute("select tapi_node_edge_point_uuid from node_edge_point_relation where resource_ptp_id = %s",
             (dst_uni_ptp,))
dst_uni_nep = tapi.fetchone()[0]
print("nep", src_uni_nep, dst_uni_nep)

# 查找 uni nep 对应的 sip
tapi.execute("select sip_uuid from sip_relation where nep_uuid = %s", (src_uni_nep,))
src_uni_sip = tapi.fetchone()[0]
tapi.execute("select sip_uuid from sip_relation where nep_uuid = %s", (dst_uni_nep,))
dst_uni_sip = tapi.fetchone()[0]
print("sip", src_uni_sip, dst_uni_sip)

tapi.execute("select uuid from topology")
topology_uuid = tapi.fetchone()[0]
print("topology_uuid", topology_uuid)

request["uuid"] = str(uuid.uuid4())
request["name"][0]["value"] = config["service_name"]
request["end-point"][0]["service-interface-point"]["service-interface-point-uuid"] = src_uni_sip
request["end-point"][0]["local-id"] = "node" + str(src_topology_node_id) + "/odu"
request["end-point"][1]["service-interface-point"]["service-interface-point-uuid"] = dst_uni_sip
request["end-point"][1]["local-id"] = "node" + str(dst_topology_node_id) + "/odu"

print("include_node:")
include_node = config["include_node"]
for node in include_node:
    tapi.execute("select tapi_node_uuid from node_relation where topology_node_id = %s", (node,))
    node_uuid = tapi.fetchone()[0]
    request["include-node"].append({"topology-uuid": topology_uuid, "node-uuid": node_uuid})
    print(node_uuid)

print("exclude_node:")
exclude_node = config["exclude_node"]
for node in exclude_node:
    tapi.execute("select tapi_node_uuid from node_relation where topology_node_id = %s", (node,))
    node_uuid = tapi.fetchone()[0]
    request["exclude-node"].append({"topology-uuid": topology_uuid, "node-uuid": node_uuid})
    print(node_uuid)

print("exclude_link:")
exclude_link = config["exclude_link"]
for link in exclude_link:
    tapi.execute("select tapi_link_uuid from link_relation where topology_link_id = %s", (link,))
    link_uuid = tapi.fetchone()[0]
    request["exclude-link"].append({"topology-uuid": topology_uuid, "link-uuid": link_uuid})
    print(link_uuid)

w_file = open("request.json", "w")
json.dump(request, w_file, indent=4)
w_file.close()
f.close()
