#!/usr/bin/env/python
# 
# Using the file system load
#
# We now assume we have a file in the same dir as this one called
# test_template.html
#
from typing import List
import os
import random
from threading import Thread
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Capture our current directory
# print ("print current file",os.path.abspath(__file__))
from drivebuildclient.AIExchangeService import AIExchangeService
from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, VehicleID
from drivebuildclient.aiExchangeMessages_pb2 import SimStateResponse, DataRequest


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(CURRENT_DIR, 'templates')
TESTCASE_DIR = os.path.join(CURRENT_DIR, 'testcases')


def load_param_to_xml(distance, speed2, testcaseID):
    pos1 = (0, 0)
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(TEMP_DIR),
                         trim_blocks=True)

    template = j2_env.get_template('criteriaA.dbc.xml')
    nameTC = "Testcase" + str(testcaseID)
    testcase_crit = template.render(tcid=nameTC, pos1x=0, pos1y=0, pos2x=0, pos2y=distance, speedcar2=speed2)
    return testcase_crit


def generate_xml_testcase(num_tc, dist, speed):
    # dist = []
    # speed = []
    # delete all old xml file
    filelist = [f for f in os.listdir(TESTCASE_DIR) if f.endswith(".xml")]
    for f in filelist:
        os.remove(os.path.join(TESTCASE_DIR, f))

    for i in range(num_tc):
        # temp_dist = random.randint(10, 60)
        # dist.append(temp_dist)
        # temp_speed = random.randint(10, 80)
        # speed.append(temp_speed)

        file_name = os.path.join(TESTCASE_DIR, "criteria" + str(i) + ".dbc.xml")
        print("file name", file_name)

        # xml_data = load_xml_criteria(temp_dist, temp_speed, i)
        xml_data = load_param_to_xml(dist[i], speed[i], i)
        # print (xml_data)
        with open(file_name, 'w') as f:
            f.write(str(xml_data))

    listTC = list(zip(dist, speed))

    return listTC


def start(service: AIExchangeService, sid: SimulationID, vid: VehicleID, requests: List[str]) -> None:
        while True:
            print(sid.sid + ": Test status: " + service.get_status(sid))
            # Wait for the simulation to request this AI
            sim_state = service.wait_for_simulator_request(sid, vid)
            print(": Request data")
            if sim_state is SimStateResponse.SimState.RUNNING:  # Check whether simulation is still running
                request= DataRequest()
                request.request_ids.extend(requests)
                data= service.request_data(sid, vid, request)  # request()
                print (data)
                 
            else:
                print(sid.sid + ": The simulation is not running anymore (Final state: "
                      + SimStateResponse.SimState.Name(sim_state) + ").")
                print(sid.sid + ": Final test result: " + service.get_result(sid))
                # Clean up everything you have to
                break    

                
# def start(sid: SimulationID, vid: VehicleID) -> None:
    # from drivebuildclient.aiExchangeMessages_pb2 import SimStateResponse, DataRequest
    # request = DataRequest()
    # request.request_ids.extend([vid.vid + "Position"])
    # while True:
        # sim_state = service.wait_for_simulator_request(sid, vid)
        # data = service.request_data(sid, vid, request)
        # print(data)
        # if sim_state != SimStateResponse.SimState.RUNNING:
            # break
                
def run_TC_DriveBuild(num_tc):
    # generate xml file

    service = AIExchangeService("defender.fim.uni-passau.de", 8383)
    result = list()
    # Send tests
    for i in range(num_tc):
        dbc_file_name = os.path.join(TESTCASE_DIR, "criteria" + str(i) + ".dbc.xml")
        dbe_file_name = os.path.join(TEMP_DIR, "environmentA.dbe.xml")
        submission_result = service.run_tests("NguyenThiThuNgan", "z.#e4V7Z", Path(dbc_file_name), Path(dbe_file_name))

        # Interact with a simulation
        if submission_result and submission_result.submissions:
            for test_name, sid in submission_result.submissions.items():
                ego_requests = ["egoPosition", "egoSpeed", "egoSteeringAngle", "egoFrontCamera", "egoLidar", "egoLaneDist"]
                non_ego_requests = ["nonEgoPosition", "nonEgoSpeed", "nonEgoSteeringAngle", "nonEgoLeftCamera", "nonEgoLidar",
                                    "nonEgoLaneDist"]
                                    
                ego_vid = VehicleID()
                ego_vid.vid = "ego"
                #ego_vehicle = Thread(target=service.wait_for_simulator_request, args=(sid, ego_vid))
                ego_vehicle = Thread(target=start, args=(service, sid, ego_vid, ego_requests))
                ego_vehicle.start()
                
                non_ego_vid = VehicleID()
                non_ego_vid.vid = "nonEgo"
                #non_ego_vehicle = Thread(target=service.wait_for_simulator_request, args=(sid, non_ego_vid))
                non_ego_vehicle = Thread(target=start, args=(service, sid, non_ego_vid, non_ego_requests))
                non_ego_vehicle.start()
                ego_vehicle.join()
                non_ego_vehicle.join()
                
                test_result = service.get_result(sid)
                print ("\n Result of testcase: ", test_result)
                result.append(test_result)
         
        else:
            print("Submitted tests were invalid.")
            print(submission_result.message.message)
            
        
            

    return result


#UNKNOWN, SUCCEEDED, FAILED or CANCELLED
def converse_result(result):
    biResult_list = list()
    biResult = -1
    for item in result:
        if item == "SUCCEEDED":
            biResult = 1
        elif item == "FAILED":
            biResult = 0
        else:
            biResult = -1
        
        if biResult == -1:
            print("\n The testcase couldn't run successfully \n")
            return 0
        biResult_list.append(biResult)
    return biResult_list


# num_tc = 1
# dist = [100]
# speed = [150]
# generate_xml_testcase(num_tc, dist, speed)
# run_TC_DriveBuild(num_tc)
    
    
