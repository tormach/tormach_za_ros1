def expand_wildcards(input_str_list):
    robot_configs = [
        "NUT",
        "NDT",
        "NUB",
        "NDB",
        "FUT",
        "FDT",
        "FUB",
        "FDB",
    ]
    result = set()  # Use a set to store unique configurations
    for config_str in input_str_list:
        if '*' in config_str:
            matching_configs = robot_configs
            for i, char in enumerate(config_str):
                if char != '*':
                    matching_configs = [
                        config
                        for config in matching_configs
                        if config[i] == char
                    ]
            result.update(
                matching_configs
            )  # Use update() to add elements to the set
        else:
            result.add(config_str)  # Use add() to add an element to the set
    return list(result)  # Convert the set to a list before returning
