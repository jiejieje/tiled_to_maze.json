import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from collections import defaultdict
import threading
import queue
import re

def update_spatial_data_in_agents(spatial_tree_filepath, agents_base_folder_path, progress_queue=None):
    """
    Updates the 'spatial' data in agent.json files based on a spatial_tree.json file.
    """
    try:
        if progress_queue:
            progress_queue.put(("update_status", "开始更新Agent空间数据..."))
            progress_queue.put(("update_progress", 10))

        # Construct absolute paths if relative paths are given
        # Assuming this script (tiled_to_maze.py) is in the 'generative_agents' directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir) # Goes up one level to the project root

        if not os.path.isabs(spatial_tree_filepath):
            spatial_tree_filepath = os.path.join(project_root, spatial_tree_filepath)
        
        if not os.path.isabs(agents_base_folder_path):
            agents_base_folder_path = os.path.join(project_root, agents_base_folder_path)

        if progress_queue:
            progress_queue.put(("update_status", f"读取空间树文件: {os.path.basename(spatial_tree_filepath)}"))
            progress_queue.put(("update_progress", 20))

        with open(spatial_tree_filepath, 'r', encoding='utf-8') as f:
            spatial_data_source = json.load(f)

        if 'spatial' not in spatial_data_source:
            error_msg = f"错误: 'spatial' 键未在 {spatial_tree_filepath} 中找到"
            if progress_queue:
                progress_queue.put(("update_status", error_msg))
                progress_queue.put(("update_progress", 0))
            print(error_msg)
            return False, error_msg

        new_spatial_info = spatial_data_source['spatial']

        if progress_queue:
            progress_queue.put(("update_status", "遍历Agent文件夹..."))
            progress_queue.put(("update_progress", 30))

        updated_files_count = 0
        skipped_files_count = 0
        error_files_count = 0
        total_agent_folders = [name for name in os.listdir(agents_base_folder_path) if os.path.isdir(os.path.join(agents_base_folder_path, name))]
        num_agent_folders = len(total_agent_folders)

        for i, agent_folder_name in enumerate(total_agent_folders):
            agent_folder_path = os.path.join(agents_base_folder_path, agent_folder_name)
            agent_json_path = os.path.join(agent_folder_path, 'agent.json')

            if progress_queue and num_agent_folders > 0:
                progress_percent = 30 + int((i / num_agent_folders) * 60) # 30% to 90%
                progress_queue.put(("update_progress", progress_percent))
                progress_queue.put(("update_status", f"处理Agent: {agent_folder_name} ({i+1}/{num_agent_folders})"))

            if os.path.isfile(agent_json_path):
                try:
                    with open(agent_json_path, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    
                    agent_data['spatial'] = new_spatial_info

                    with open(agent_json_path, 'w', encoding='utf-8') as f:
                        json.dump(agent_data, f, ensure_ascii=False, indent=2)
                    # print(f"Successfully updated {agent_json_path}")
                    if progress_queue:
                         progress_queue.put(("log_message", f"成功更新: {os.path.basename(agent_folder_name)}/agent.json"))
                    updated_files_count += 1
                except json.JSONDecodeError:
                    error_msg = f"错误: 无法解码JSON {agent_json_path}. 跳过此文件."
                    if progress_queue:
                        progress_queue.put(("log_message", error_msg))
                    print(error_msg)
                    error_files_count += 1
                    continue
                except Exception as e:
                    error_msg = f"读取/写入 {agent_json_path} 时出错: {e}. 跳过此文件."
                    if progress_queue:
                        progress_queue.put(("log_message", error_msg))
                    print(error_msg)
                    error_files_count += 1
                    continue
            else:
                warn_msg = f"警告: agent.json 未在 {agent_folder_path} 中找到"
                if progress_queue:
                    progress_queue.put(("log_message", warn_msg))
                # print(warn_msg)
                skipped_files_count +=1
        
        final_status_msg = f"Agent空间数据更新完成. 更新: {updated_files_count}, 跳过: {skipped_files_count}, 错误: {error_files_count}."
        if progress_queue:
            progress_queue.put(("update_status", final_status_msg))
            progress_queue.put(("update_progress", 100))
        print(final_status_msg)
        return True, final_status_msg

    except FileNotFoundError as e:
        error_msg = f"错误: 文件未找到 - {e}"
        if progress_queue:
            progress_queue.put(("update_status", error_msg))
            progress_queue.put(("update_progress", 0))
        print(error_msg)
        return False, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"错误: JSON解码失败 - {e}"
        if progress_queue:
            progress_queue.put(("update_status", error_msg))
            progress_queue.put(("update_progress", 0))
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"更新Agent空间数据时发生意外错误: {e}"
        if progress_queue:
            progress_queue.put(("update_status", error_msg))
            progress_queue.put(("update_progress", 0))
        print(error_msg)
        return False, error_msg

def convert_tiled_to_maze(tiled_filepath, maze_filepath, progress_queue=None):
    """
    将 JSON 地图文件转换为 maze.json 格式。
    """
    try:
        if progress_queue:
            progress_queue.put(("update_status", "正在读取Tiled文件..."))
            progress_queue.put(("update_progress", 10))
            
        with open(tiled_filepath, 'r', encoding='utf-8') as f:
            tiled_data = json.load(f)

        if progress_queue:
            progress_queue.put(("update_status", "正在创建基础Maze结构..."))
            progress_queue.put(("update_progress", 20))
            
        maze_data = {
            "world": "the Ville",
            "tile_size": tiled_data["tilewidth"],
            "size": [tiled_data["height"], tiled_data["width"]],
            "map": {
                "asset": "map",
                "tileset_groups": {
                    "group_1": []
                },
                "layers": [],
                "collision_tiles": [2843] #  这里可以根据你的 Tiled 地图配置进行调整
            },
            "camera": {
                "zoom_factor": 1,
                "zoom_range": [
                    0.5,
                    10,
                    0.01
                ]
            },
            "tile_address_keys": [
                "world",
                "sector",
                "arena",
                "game_object"
            ],
            "tiles": []
        }

        # 处理 tilesets
        if progress_queue:
            progress_queue.put(("update_status", "处理图块集..."))
            progress_queue.put(("update_progress", 30))
            
        tiled_dir = os.path.dirname(tiled_filepath)
        for tileset in tiled_data["tilesets"]:
            if "source" in tileset:
                # 处理外部 tileset
                tsj_path = os.path.join(tiled_dir, tileset["source"].replace("\\", "/"))
                try:
                    with open(tsj_path, 'r', encoding='utf-8') as tsj_f:
                        external_tileset = json.load(tsj_f)
                    image_path = external_tileset.get("image")
                    if not image_path:
                        raise ValueError(f"External tileset {tileset['source']} missing 'image' key")
                    tileset_name = os.path.basename(image_path).split('.')[0]
                except FileNotFoundError:
                    # Fallback: use basename of source if tsj not found
                    source_basename = os.path.basename(tileset["source"])
                    tileset_name = os.path.splitext(source_basename)[0]
                    if progress_queue:
                        progress_queue.put(("log_message", f"警告: 未找到外部tileset {tsj_path}, 使用回退名称 {tileset_name}"))
            else:
                # 内部 tileset
                image_path = tileset.get("image")
                if not image_path:
                    raise ValueError("Tileset missing 'image' key")
                tileset_name = os.path.basename(image_path).split('.')[0]
            
            maze_data["map"]["tileset_groups"]["group_1"].append(tileset_name)

        # 分离不同类型的图层
        address_layers = []
        world_layer = None
        collision_layer = None

        if progress_queue:
            progress_queue.put(("update_status", "识别图层类型..."))
            progress_queue.put(("update_progress", 40))
            
        for layer in tiled_data["layers"]:
            # 识别原始命名的图层
            if layer["name"].startswith("sector-") or layer["name"].startswith("arena-") or layer["name"].startswith("object-"):
                address_layers.append(layer)
            # 增加对数字开头图层的识别
            elif layer["name"].startswith("1"):
                # 将以1开头的图层当作sector处理，但保持原始名称
                layer["address_type"] = "sector"
                address_layers.append(layer)
            elif layer["name"].startswith("2"):
                # 将以2开头的图层当作arena处理，但保持原始名称
                layer["address_type"] = "arena"
                address_layers.append(layer)
            elif layer["name"].startswith("3"):
                # 将以3开头的图层当作object处理，但保持原始名称
                layer["address_type"] = "object"
                address_layers.append(layer)
            elif layer["name"] == "world-xy":
                world_layer = layer
            elif layer["name"] == "collisions":
                collision_layer = layer

        # 首先处理 address layers (sector-XXX, arena-XXX, object-XXX)
        if progress_queue:
            progress_queue.put(("update_status", "处理地址图层..."))
            progress_queue.put(("update_progress", 50))
            
        total_layers = len(address_layers)
        for idx, layer in enumerate(address_layers):
            if progress_queue and total_layers > 0:
                progress_percent = 50 + (idx / total_layers) * 15
                progress_queue.put(("update_progress", progress_percent))
                progress_queue.put(("update_status", f"处理图层 {layer['name']}..."))
                
            maze_layer = {
                "name": layer["name"],
                "tileset_group": "group_1"
            }
            if "Foreground" in layer["name"]:
                maze_layer["depth"] = 2
            maze_data["map"]["layers"].append(maze_layer)

            layer_width = tiled_data["width"]
            layer_data = layer["data"]
            layer_name = layer["name"] #  获取图层名称作为地址或物体信息
            
            # 使用原始图层名称作为地址信息
            address_name = layer_name

            address_type = None # 新增：用于存储地址类型
            if layer_name.startswith("sector-"):
                address_type = "sector"
            elif layer_name.startswith("arena-"):
                address_type = "arena"
            elif layer_name.startswith("object-"):
                address_type = "game_object"
            elif "address_type" in layer:
                # 处理数字前缀的图层
                address_type = layer["address_type"]

            for index, tile_id in enumerate(layer_data):
                if tile_id != 0:
                    x = index % layer_width
                    y = index // layer_width
                    found_tile = False
                    for tile in maze_data["tiles"]:
                        if tile["coord"] == [x, y]:
                            # 使用可能修改过的address_name而不是layer_name
                            if address_name not in tile["address"]: # 避免重复添加
                                tile["address"].append(address_name) #  如果瓦片已存在，添加地址/物体信息
                            found_tile = True
                            break
                    if not found_tile:
                        #  如果瓦片不存在 (可能碰撞图层没有覆盖所有区域), 创建新瓦片并添加地址/物体信息
                        new_tile_address = [address_name] # 使用可能修改过的address_name
                        maze_data["tiles"].append({
                            "coord": [x, y],
                            "address": new_tile_address #  如果瓦片不存在，初始化 address 列表并添加图层名称
                        })

        # 然后处理 world-xy layer
        if progress_queue:
            progress_queue.put(("update_status", "处理世界坐标图层..."))
            progress_queue.put(("update_progress", 70))
            
        if world_layer:
            maze_layer = {
                "name": world_layer["name"],
                "tileset_group": "group_1"
            }
            maze_data["map"]["layers"].append(maze_layer)

            layer_width = tiled_data["width"]
            layer_data = world_layer["data"]
            layer_name = world_layer["name"] #  获取图层名称作为地址或物体信息

            for index, tile_id in enumerate(layer_data):
                if tile_id != 0:
                    x = index % layer_width
                    y = index // layer_width
                    found_tile = False
                    for tile in maze_data["tiles"]:
                        if tile["coord"] == [x, y]:
                            found_tile = True
                            break
                    if not found_tile:
                        #  如果瓦片不存在, 创建新瓦片 (world-xy 图层不添加 address 信息)
                        maze_data["tiles"].append({
                            "coord": [x, y],
                            "address": [] # world-xy 图层不添加 address 信息
                        })


        # 最后处理碰撞图层，合并碰撞信息到已存在的瓦片数据
        if progress_queue:
            progress_queue.put(("update_status", "处理碰撞图层..."))
            progress_queue.put(("update_progress", 80))
            
        if collision_layer:
            maze_layer = {
                "name": collision_layer["name"],
                "tileset_group": "group_1",
                "depth": -1,
                "collision": {
                    "exclusion": [-1]
                }
            }
            maze_data["map"]["layers"].append(maze_layer)

            layer_width = tiled_data["width"]
            layer_data = collision_layer["data"]
            layer_name = collision_layer["name"]

            for index, tile_id in enumerate(layer_data):
                if tile_id != 0:
                    x = index % layer_width
                    y = index // layer_width
                    found_tile = False
                    for tile in maze_data["tiles"]:
                        if tile["coord"] == [x, y]:
                            if "address" in tile: # 确保 address 键存在
                                tile["collision"] = True #  如果瓦片已存在，添加碰撞信息
                            else:
                                tile["collision"] = True # 如果瓦片存在但是没有 address 键，添加 collision
                            found_tile = True
                            break
                    if not found_tile:
                        #  如果瓦片不存在 (虽然理论上在前面的步骤中应该已经创建了所有瓦片),  为了完整性，仍然创建新瓦片并添加碰撞信息
                        maze_data["tiles"].append({
                            "coord": [x, y],
                            "address": [], # 碰撞层本身不添加地址信息
                            "collision": True #  如果瓦片不存在，创建新瓦片并添加碰撞信息
                        })

        if progress_queue:
            progress_queue.put(("update_status", "写入Maze文件..."))
            progress_queue.put(("update_progress", 90))
            
        with open(maze_filepath, 'w', encoding='utf-8') as outfile:
            json.dump(maze_data, outfile, indent=4, ensure_ascii=False)

        if progress_queue:
            progress_queue.put(("update_progress", 100))
            progress_queue.put(("update_status", "Maze文件创建完成!"))
            
        return True, maze_data  # 转换成功并返回maze数据

    except Exception as e:
        if progress_queue:
            progress_queue.put(("update_status", f"错误: {str(e)}"))
            progress_queue.put(("update_progress", 0))
        return False, str(e)  # 转换失败并返回错误信息

def get_overlap_ratio(coords1, coords2):
    """计算两个坐标集合的重叠比例"""
    overlap = coords1.intersection(coords2)
    return len(overlap) / len(coords1)

def build_location_hierarchy(locations):
    hierarchy = {}
    processed = set()
    
    # 按数字前缀分组
    prefix_1_locations = {k:v for k,v in locations.items() if k.startswith("1")}
    prefix_2_locations = {k:v for k,v in locations.items() if k.startswith("2")}
    prefix_3_locations = {k:v for k,v in locations.items() if k.startswith("3")}
    
    # 构建层级关系
    for loc1_name, coords1 in prefix_1_locations.items():
        hierarchy[loc1_name] = {}
        processed.add(loc1_name)
        
        # 查找相交的2级区域
        for loc2_name, coords2 in prefix_2_locations.items():
            if loc2_name in processed:
                continue
                
            # 如果有重叠（使用更宽松的判断）
            if len(coords1.intersection(coords2)) > 0:
                hierarchy[loc1_name][loc2_name] = []
                processed.add(loc2_name)
                
                # 查找相交的3级物体
                for loc3_name, coords3 in prefix_3_locations.items():
                    if loc3_name in processed:
                        continue
                        
                    if len(coords2.intersection(coords3)) > 0:
                        hierarchy[loc1_name][loc2_name].append(loc3_name)
                        processed.add(loc3_name)
    
    return hierarchy

def convert_maze_to_tree(maze_data, progress_queue=None):
    """将迷宫数据转换为空间树结构
    
    Args:
        maze_data: 迷宫JSON数据
        progress_queue: 用于更新进度的队列
    Returns:
        (bool, object) 转换成功与否及转换结果或错误信息
    """
    try:
        if progress_queue:
            progress_queue.put(("update_status", "开始创建空间树..."))
            progress_queue.put(("update_progress", 50))
            
        # 初始化空间树结构
        spatial_tree = {
            "spatial": {
                "address": {
                    "living_area": [maze_data["world"]]
                },
                "tree": {
                    maze_data["world"]: {}
                }
            }
        }

        if progress_queue:
            progress_queue.put(("update_status", "收集坐标地址信息..."))
            progress_queue.put(("update_progress", 60))
            
        # 用于存储每个坐标的地址信息
        coord_addresses = defaultdict(list)
        
        # 遍历所有地块,收集地址信息
        for tile in maze_data["tiles"]:
            if "address" in tile:
                coord = tuple(tile["coord"])
                coord_addresses[coord].extend(tile["address"])

        if progress_queue:
            progress_queue.put(("update_status", "分离地点和物体..."))
            progress_queue.put(("update_progress", 70))
            
        # 分离地点和物体
        locations = {}  # 存储地点信息
        objects = defaultdict(list)  # 存储物体信息

        for coord, addresses in coord_addresses.items():
            for addr in addresses:
                # 原始格式检查
                if addr.startswith("sector-") or addr.startswith("arena-"):
                    # 处理地点
                    location_name = addr
                    if location_name not in locations:
                        locations[location_name] = set()
                    locations[location_name].add(coord)
                elif addr.startswith("object-"):
                    # 处理物体
                    obj_name = addr
                    for loc_name, loc_coords in locations.items():
                        if coord in loc_coords:
                            objects[loc_name].append(obj_name)
                # 新增：处理数字前缀的地址
                elif addr.startswith("1"):
                    # 处理以1开头的图层为sector类型
                    location_name = addr
                    if location_name not in locations:
                        locations[location_name] = set()
                    locations[location_name].add(coord)
                elif addr.startswith("2"):
                    # 处理以2开头的图层为arena类型
                    location_name = addr
                    if location_name not in locations:
                        locations[location_name] = set()
                    locations[location_name].add(coord)
                elif addr.startswith("3"):
                    # 处理以3开头的图层为object类型
                    obj_name = addr
                    for loc_name, loc_coords in locations.items():
                        if coord in loc_coords:
                            objects[loc_name].append(obj_name)

        if progress_queue:
            progress_queue.put(("update_status", "构建地点层级关系..."))
            progress_queue.put(("update_progress", 80))
            
        # 构建地点层级关系
        location_hierarchy = build_location_hierarchy(locations)
        
        if progress_queue:
            progress_queue.put(("update_status", "构建最终树结构..."))
            progress_queue.put(("update_progress", 90))
            
        # 构建最终的树结构
        def build_tree(hierarchy, objects):
            tree = {}
            for loc_name, children in hierarchy.items():
                base_name = loc_name
                if children:  # 如果有子地点
                    tree[base_name] = build_tree(children, objects)
                else:  # 如果是叶子节点
                    location_objects = list(set(objects[base_name]))
                    tree[base_name] = location_objects
            return tree

        # 构建树结构
        world_tree = spatial_tree["spatial"]["tree"][maze_data["world"]]
        world_tree.update(build_tree(location_hierarchy, objects))
        
        if progress_queue:
            progress_queue.put(("update_status", "空间树创建完成!"))
            progress_queue.put(("update_progress", 100))
            
        return True, spatial_tree
    except Exception as e:
        if progress_queue:
            progress_queue.put(("update_status", f"错误: {str(e)}"))
            progress_queue.put(("update_progress", 0))
        return False, str(e)

def remove_number_prefix(data):
    """
    移除JSON数据中的数字前缀
    
    Args:
        data: 要处理的数据（maze.json或spatial_tree.json）
    Returns:
        处理后的数据
    """
    # 递归处理dict中的所有键和值
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            # 处理key是字符串且以数字开头的情况
            if isinstance(key, str) and re.match(r'^[123]\w+', key):
                # 移除数字前缀，把"1xxx"、"2xxx"、"3xxx"改为"xxx"
                new_key = re.sub(r'^[123]', '', key)
                new_data[new_key] = remove_number_prefix(value)
            else:
                new_data[key] = remove_number_prefix(value)
        return new_data
    # 递归处理列表中的所有元素
    elif isinstance(data, list):
        new_data = []
        for item in data:
            if isinstance(item, str) and re.match(r'^[123]\w+', item):
                # 移除数字前缀，把"1xxx"、"2xxx"、"3xxx"改为"xxx"
                new_item = re.sub(r'^[123]', '', item)
                new_data.append(new_item)
            else:
                new_data.append(remove_number_prefix(item))
        return new_data
    else:
        return data

def create_simplified_tiled(tiled_data):
    """
    创建Tiled地图数据的简化版本，移除大型数据字段，减小文件体积
    
    Args:
        tiled_data: Tiled格式的地图数据
    Returns:
        简化后的数据
    """
    # 创建一个深拷贝，避免修改原始数据
    import copy
    simplified_data = copy.deepcopy(tiled_data)
    
    # 移除layers中的data字段（这通常是最大的部分）
    if "layers" in simplified_data:
        for layer in simplified_data["layers"]:
            if "data" in layer:
                # 完全移除data字段
                del layer["data"]
                layer["__note__"] = "Data字段已被移除以减小文件体积，此文件仅用于参考"
    
    # 添加说明
    simplified_data["__simplified_note__"] = "此文件为简化版，已移除图层数据等大型字段。适合AI分析或修改。"
    
    return simplified_data

class TiledToSpatialTreeConverter:
    def __init__(self, master):
        self.master = master
        self.master.title("Tiled地图到空间树转换工具")
        self.master.geometry("800x600")
        
        # 初始化文件路径变量
        self.tiled_file_path = tk.StringVar()
        self.output_dir_path = tk.StringVar()
        self.output_dir_path.set(os.getcwd())  # 默认为当前目录
        self.maze_filename = tk.StringVar()
        self.maze_filename.set("maze.json")
        self.tree_filename = tk.StringVar()
        self.tree_filename.set("spatial_tree.json")
        
        # 添加更新Agent空间数据按钮
        self.update_agents_spatial_data_button = tk.Button(self.master, text="更新Agent空间数据", command=self.run_update_agents_spatial_data, state=tk.DISABLED)
        self.update_agents_spatial_data_button.pack(pady=5)
        
        # 添加移除数字前缀选项
        self.remove_prefix = tk.BooleanVar()
        self.remove_prefix.set(True)  # 默认勾选
        
        # 添加创建简约信息选项
        self.create_simplified = tk.BooleanVar()
        self.create_simplified.set(True)  # 默认勾选
        
        # 创建进度队列
        self.progress_queue = queue.Queue()
        
        # 创建界面组件
        self.create_widgets()
        
        # 设置周期性检查队列的任务
        self.check_queue()

    def run_update_agents_spatial_data(self):
        # 禁用按钮，防止重复点击
        self.update_agents_spatial_data_button.config(state=tk.DISABLED)
        self.status_label.config(text="正在更新Agent空间数据...")
        self.progress_bar['value'] = 0

        # 启动后台线程执行更新操作
        threading.Thread(target=self.perform_agent_spatial_update, daemon=True).start()

    def perform_agent_spatial_update(self):
        # 定义默认路径，这些路径相对于项目根目录
        # 项目根目录是 tiled_to_maze.py 所在目录的上一级
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)

        default_spatial_tree_filename = "spatial_tree.json"
        default_agents_base_folder = os.path.join("generative_agents", "frontend", "static", "assets", "village", "agents")

        # 获取输出目录，如果为空，则使用项目根目录
        output_dir = self.output_dir_path.get()
        if not output_dir:
            output_dir = project_root
        
        # 构造 spatial_tree.json 的完整路径
        # 优先使用输出目录下的 spatial_tree.json，如果不存在，则使用项目根目录下的
        spatial_tree_path_in_output = os.path.join(output_dir, self.tree_filename.get() or default_spatial_tree_filename)
        spatial_tree_path_in_root = os.path.join(project_root, self.tree_filename.get() or default_spatial_tree_filename)

        if os.path.exists(spatial_tree_path_in_output):
            spatial_tree_filepath = spatial_tree_path_in_output
        elif os.path.exists(spatial_tree_path_in_root):
            spatial_tree_filepath = spatial_tree_path_in_root
        else:
            self.progress_queue.put(("update_status", f"错误: 未找到 {default_spatial_tree_filename} 文件"))
            self.progress_queue.put(("update_progress", 0))
            # 重新启用按钮
            self.progress_queue.put(("enable_button", "update_agents_spatial_data_button"))
            return

        # agents_base_folder_path 总是相对于项目根目录
        agents_base_folder_path = os.path.join(project_root, default_agents_base_folder)

        if not os.path.exists(agents_base_folder_path):
            self.progress_queue.put(("update_status", f"错误: Agent基础文件夹 {agents_base_folder_path} 不存在"))
            self.progress_queue.put(("update_progress", 0))
            self.progress_queue.put(("enable_button", "update_agents_spatial_data_button"))
            return

        success, message = update_spatial_data_in_agents(spatial_tree_filepath, agents_base_folder_path, self.progress_queue)
        
        # 确保在主线程中更新UI
        self.progress_queue.put(("enable_button", "update_agents_spatial_data_button"))
        if success:
            self.progress_queue.put(("log_message", "Agent空间数据更新成功完成。"))
        else:
            self.progress_queue.put(("log_message", f"Agent空间数据更新失败: {message}"))

    def create_widgets(self):
        # Tiled文件选择
        tiled_frame = tk.Frame(self.master)
        tiled_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tiled_label = tk.Label(tiled_frame, text="Tiled导出的地图json文件:", width=15, anchor="w")
        tiled_label.pack(side=tk.LEFT, padx=5)
        
        tiled_entry = tk.Entry(tiled_frame, textvariable=self.tiled_file_path, width=50)
        tiled_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        tiled_button = tk.Button(tiled_frame, text="选择文件", command=self.select_tiled_file)
        tiled_button.pack(side=tk.LEFT, padx=5)
        
        # 输出目录选择
        output_dir_frame = tk.Frame(self.master)
        output_dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        output_dir_label = tk.Label(output_dir_frame, text="输出目录:", width=15, anchor="w")
        output_dir_label.pack(side=tk.LEFT, padx=5)
        
        output_dir_entry = tk.Entry(output_dir_frame, textvariable=self.output_dir_path, width=50)
        output_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        output_dir_button = tk.Button(output_dir_frame, text="选择目录", command=self.select_output_dir)
        output_dir_button.pack(side=tk.LEFT, padx=5)
        
        # Maze文件名设置
        maze_frame = tk.Frame(self.master)
        maze_frame.pack(fill=tk.X, padx=10, pady=10)
        
        maze_label = tk.Label(maze_frame, text="Maze文件名:", width=15, anchor="w")
        maze_label.pack(side=tk.LEFT, padx=5)
        
        maze_entry = tk.Entry(maze_frame, textvariable=self.maze_filename, width=50)
        maze_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 空间树文件名设置
        tree_frame = tk.Frame(self.master)
        tree_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tree_label = tk.Label(tree_frame, text="空间树文件名:", width=15, anchor="w")
        tree_label.pack(side=tk.LEFT, padx=5)
        
        tree_entry = tk.Entry(tree_frame, textvariable=self.tree_filename, width=50)
        tree_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 添加选项复选框
        options_frame = tk.Frame(self.master)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        prefix_check = tk.Checkbutton(options_frame, text="移除名称中的数字前缀（将1xxx、2xxx、3xxx变为xxx）", 
                                    variable=self.remove_prefix)
        prefix_check.pack(anchor=tk.W, padx=5)
        
        simplified_check = tk.Checkbutton(options_frame, text="生成简约信息文件（适合AI修改，移除大数据字段）", 
                                        variable=self.create_simplified)
        simplified_check.pack(anchor=tk.W, padx=5)
        
        # 添加进度条和状态标签
        progress_frame = tk.Frame(self.master)
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(progress_frame, text="准备就绪", anchor="w")
        self.status_label.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 转换按钮
        convert_button = tk.Button(self.master, text="一键转换 Tiled → Maze → 空间树", 
                                 command=self.start_conversion, bg="#4CAF50", fg="white",
                                 font=("Arial", 12, "bold"), height=2)
        convert_button.pack(pady=20)
        
        # 日志文本框
        log_frame = tk.Frame(self.master)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, width=80, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.log_text.yview)
        
        # 初始日志信息
        self.log_text.insert(tk.END, "欢迎使用Tiled地图转换工具\n")
        self.log_text.insert(tk.END, "请选择Tiled地图导出的json文件并点击'一键转换'按钮开始转换\n")
    
    def check_queue(self):
        """检查进度队列并更新UI"""
        try:
            while True:
                message = self.progress_queue.get_nowait()
                if message[0] == "update_progress":
                    self.progress_bar["value"] = message[1]
                elif message[0] == "update_status":
                    self.status_label.config(text=message[1])
                    self.log_text.insert(tk.END, f"{message[1]}\n")
                    self.log_text.see(tk.END)
                self.progress_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # 每100毫秒检查一次队列
            self.master.after(100, self.check_queue)
        
    def select_tiled_file(self):
        """选择Tiled地图文件"""
        file_path = filedialog.askopenfilename(
            title="选择Tiled地图文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            self.tiled_file_path.set(file_path)
            self.log_text.insert(tk.END, f"已选择Tiled地图文件: {file_path}\n")
            self.log_text.see(tk.END)
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(
            title="选择输出目录"
        )
        if dir_path:
            self.output_dir_path.set(dir_path)
            self.log_text.insert(tk.END, f"已选择输出目录: {dir_path}\n")
            self.log_text.see(tk.END)
    
    def conversion_thread(self, tiled_file, maze_file, tree_file):
        """在单独的线程中运行转换过程"""
        try:
            # 步骤1: 读取Tiled文件
            self.progress_queue.put(("update_status", "正在读取Tiled文件..."))
            self.progress_queue.put(("update_progress", 5))
            
            # 首先读取原始Tiled文件内容
            try:
                with open(tiled_file, 'r', encoding='utf-8') as f:
                    tiled_data = json.load(f)
                    
                # 如果选择创建简约信息文件，为原始Tiled文件创建简约版
                if self.create_simplified.get():
                    self.progress_queue.put(("update_status", "创建Tiled地图简约信息文件..."))
                    
                    # 获取不带扩展名的文件名
                    file_name = os.path.splitext(os.path.basename(tiled_file))[0]
                    simplified_tiled_path = os.path.join(self.output_dir_path.get(), f"{file_name}_简约信息.json")
                    
                    # 创建简约版Tiled数据
                    simplified_tiled_data = create_simplified_tiled(tiled_data)
                    
                    # 保存简约版Tiled文件
                    with open(simplified_tiled_path, 'w', encoding='utf-8') as f:
                        json.dump(simplified_tiled_data, f, indent=2, ensure_ascii=False)
                        
                    self.progress_queue.put(("update_status", f"已保存Tiled地图简约信息文件: {simplified_tiled_path}"))
            except Exception as e:
                self.progress_queue.put(("update_status", f"读取或处理Tiled文件时出错: {str(e)}"))
                self.progress_queue.put(("update_progress", 0))
                return
            
            # 步骤2: Tiled转Maze
            self.progress_queue.put(("update_status", "======== 第一步: Tiled → Maze ========"))
            self.progress_queue.put(("update_progress", 15))
            
            success, maze_data = convert_tiled_to_maze(tiled_file, maze_file, self.progress_queue)
            
            if not success:
                self.progress_queue.put(("update_status", f"转换失败: {maze_data}"))
                return
            
            self.progress_queue.put(("update_status", f"成功: Tiled地图已转换为Maze文件 {maze_file}"))
            
            # 步骤3: Maze转空间树（使用原始带前缀的数据）
            self.progress_queue.put(("update_status", "======== 第二步: Maze → 空间树 ========"))
            
            success, tree_data = convert_maze_to_tree(maze_data, self.progress_queue)
            
            if not success:
                self.progress_queue.put(("update_status", f"转换失败: {tree_data}"))
                return
            
            # 如果选择去除前缀
            if self.remove_prefix.get():
                self.progress_queue.put(("update_status", "正在移除数字前缀..."))
                
                # 移除数字前缀
                maze_data = remove_number_prefix(maze_data)
                tree_data = remove_number_prefix(tree_data)
                
                # 重新写入Maze文件(覆盖原来的)
                with open(maze_file, 'w', encoding='utf-8') as f:
                    json.dump(maze_data, f, indent=4, ensure_ascii=False)
            
            # 写入空间树文件
            with open(tree_file, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2, ensure_ascii=False)
            
            self.progress_queue.put(("update_status", f"已保存文件: {maze_file} 和 {tree_file}"))
            self.progress_queue.put(("update_status", "======== 转换完成 ========"))
            self.progress_queue.put(("update_progress", 100))
            
            # 使用主线程显示消息框
            msg = f"转换完成!\n\nTiled → Maze: {maze_file}\nMaze → 空间树: {tree_file}"
            if self.create_simplified.get():
                file_name = os.path.splitext(os.path.basename(tiled_file))[0]
                msg += f"\nTiled地图简约信息: {file_name}_简约信息.json"
            if self.remove_prefix.get():
                msg += "\n\n已移除所有数字前缀。"
            
            self.master.after(0, lambda: messagebox.showinfo("成功", msg))
            
        except Exception as e:
            self.progress_queue.put(("update_status", f"转换过程中发生错误: {str(e)}"))
            self.progress_queue.put(("update_progress", 0))
            # 使用主线程显示错误消息框
            self.master.after(0, lambda: messagebox.showerror("错误", f"转换失败: {str(e)}"))
    
    def start_conversion(self):
        """开始转换流程"""
        tiled_file = self.tiled_file_path.get()
        output_dir = self.output_dir_path.get()
        maze_file = os.path.join(output_dir, self.maze_filename.get())
        tree_file = os.path.join(output_dir, self.tree_filename.get())
        
        if not tiled_file:
            messagebox.showerror("错误", "请选择Tiled地图文件")
            return
        
        # 重置进度条
        self.progress_bar["value"] = 0
        self.status_label.config(text="开始转换...")
        
        # 在新线程中运行转换过程
        conversion_thread = threading.Thread(
            target=self.conversion_thread, 
            args=(tiled_file, maze_file, tree_file)
        )
        conversion_thread.daemon = True  # 设置为守护线程，这样当主程序退出时，线程也会退出
        conversion_thread.start()

# 运行应用程序
if __name__ == "__main__":
    root = tk.Tk()
    app = TiledToSpatialTreeConverter(root)
    root.mainloop()
