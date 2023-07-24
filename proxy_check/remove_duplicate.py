with open('proxy_list.txt', 'r') as file:
    lines = file.readlines()
    unique_lines = list(set(lines))
    with open('proxy_list.txt', 'w') as file:
        file.writelines(unique_lines)
