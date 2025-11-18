import logging
import requests
import time
import config_loader

loaded_config = config_loader.load_config()
time_before_retry = loaded_config.time_before_retry
max_errors_allowed = loaded_config.max_errors_allowed

error_count = 0

def error_counter(error_count: int) -> tuple[int, int]:
    error_count = error_count+1
    remaining_errors = max_errors_allowed-error_count

    return(error_count, remaining_errors)

def handle_request_error(request_type: str="get", request_url: str=None, request_data: any=None, request_json: any=None, request_params: any=None, request_headers: any=None, status_type_ok: list=[200] ) -> object:
    
    time_before_retry = 60
    max_errors_allowed = 3
    error_count = 0

    while error_count < max_errors_allowed:

        try:
            if request_type == "get":
                request_response = requests.get(request_url, headers=request_headers)

            elif request_type == "post":
                request_response = requests.post(request_url, data=request_data, json=request_json, params=request_params)

            elif request_type == "patch":
                request_response = requests.patch(request_url, data=request_data, json=request_json, params=request_params)

            elif request_type == "delete":
                request_response = requests.delete(request_url, params=request_params)


            if request_response.status_code in status_type_ok:
                return request_response
            
            else:
                error_count, remaining_errors = error_counter(error_count)

                logging.error("unable to complete request of type: %s with url: %s and expected status return: %s response: %s trying %s more times and waiting for %s seconds",request_type, request_url, str(status_type_ok), request_response, remaining_errors , time_before_retry)
                
                if error_count != max_errors_allowed:
                    time.sleep(time_before_retry)

        except Exception as e:
                error_count, remaining_errors = error_counter(error_count)

                logging.error("unable to complete request of type: %s with url: %s and expected status return: %s exception: %s trying %s more times and waiting for %s seconds",request_type, request_url, str(status_type_ok), e, remaining_errors , time_before_retry)
                
                if error_count != max_errors_allowed:
                    time.sleep(time_before_retry)

    if error_count == max_errors_allowed:
        raise RuntimeError("Unable to complete request after trying %s times.", max_errors_allowed)