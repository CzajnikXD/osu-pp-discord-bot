import rosu_pp_py as rosu
from ossapi import Ossapi
import json
import requests
import os
import zipfile
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

recent_amount = None
manager = None

def set_manager(beatmap_manager):
    """
    Sets the BeatmapManager instance to be used by the module.
    """
    global manager
    manager = beatmap_manager

def get_manager():
    """
    Retrieves the current BeatmapManager instance.
    Raises an error if the manager is not set.
    """
    if manager is None:
        raise ValueError("Manager not set. Please initialize the BeatmapManager first.")
    return manager

def calc_lazer_pp(map, acc, n300, n100, n50, misses, combo, mods, large_tick_hits, slider_end_hits, large_tick_miss, lazer):
    """
    Calculates the performance points (PP) for a given beatmap and score attributes.
    """
    beatmap = rosu.Beatmap(path = f'{map}')
    mods_json = mod_convert(mods)
    mods_list = json.loads(mods_json)

    perf = rosu.Performance(
        accuracy=acc,
        misses=misses,
        combo=combo,
        n300=n300,
        n100=n100,
        n50=n50,
        lazer=lazer,
        large_tick_hits=large_tick_hits,
        slider_end_hits=slider_end_hits,
        hitresult_priority=rosu.HitResultPriority.BestCase,
        mods=mods_list
    )

    n300 = n300 or 0
    n100 = n100 or 0
    n50 = n50 or 0
    large_tick_miss = large_tick_miss or 0
    max_slider_end = beatmap.n_sliders
    max_slider_tick = large_tick_hits + large_tick_miss
    max_objects = beatmap.n_objects
    left_objects = max_objects - n300 - n100 - n50
    max_n300 = n300 + left_objects

    perf.set_misses(None)
    perf.set_combo(None)
    perf.set_n300(max_n300)
    perf.set_slider_end_hits(beatmap.n_sliders)
    perf.set_large_tick_hits(max_slider_tick)
    max_performance = perf.calculate(beatmap)

    full_combo = max_performance.difficulty.max_combo
    final_pp = format(max_performance.pp, ".2f")
    stars = format(max_performance.difficulty.stars, ".2f")
    if lazer != True:
        final_acc = format((300 * max_n300 + 100 * n100 + 50 * n50) / (300 * max_objects) * 100, ".2f")
    else:
        final_acc1 = format((300 * max_n300 + 100 * n100 + 50 * n50 + slider_end_hits + large_tick_hits) / ((300 * max_objects) + max_slider_end + max_slider_tick) * 100, ".2f")
        final_acc2 = format((300 * max_n300 + 100 * n100 + 50 * n50 + 300 * slider_end_hits + 10 * large_tick_hits) / ((300 * max_objects) + 300 * max_slider_end + 10 * max_slider_tick) * 100, ".2f")
        final_acc = max(final_acc1,final_acc2)

    if not len(mods) == 0:
        mods = ",".join(mod["acronym"] for mod in mods_list)
    else:
        mods = "No Mod"

    print(f'PP: {max_performance.pp} for {final_acc}% | Stars: {stars} | Mods: {mods}')
    os.remove(map)
    return final_pp, final_acc, stars, full_combo, mods

def init_api():
    """
    Initializes and returns an instance of the Ossapi client.
    """
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    api = Ossapi(client_id, client_secret)
    return api

def get_user(username):
    """
    Retrieves the user ID for a given osu username.
    """
    api = init_api()
    try:
        user_id = api.user(f'{username}').id
    except:
        user_id = None
    return user_id

def get_username(user_id):
    """
    Retrieves the username and avatar URL for a given osu user ID.
    """
    api = init_api()
    username = api.user(f'{user_id}').username
    avatar_url = api.user(f'{user_id}').avatar_url
    return username, avatar_url

def get_recent_activity(user_id,limit):
    """
    Retrieves the recent scores and the total amount of different scores for a given osu user ID.
    """
    api = init_api()
    recent = api.user_scores(user_id = user_id, limit=limit, type="recent", include_fails = True, legacy_only=False)
    recent_amount = len(recent)
    return recent, recent_amount

def get_beatmap(recent, limit_number):
    """
    Retrieves beatmap information from the recent activity.
    """
    version = recent[limit_number].beatmap.version
    beatmapset = recent[limit_number].beatmap.beatmapset_id
    title = recent[limit_number].beatmapset.title
    cover = recent[limit_number].beatmapset.covers.list_2x
    return beatmapset, version, title, cover

def get_recent_score(recent, limit_number):
    """
    Retrieves the score details from the recent activity.
    """
    max_combo = recent[limit_number].max_combo
    accuracy = recent[limit_number].accuracy
    statistics = recent[limit_number].statistics
    mods = recent[limit_number].mods
    grade = recent[limit_number].rank
    large_tick_hits = statistics.large_tick_hit or 0
    large_tick_miss = statistics.large_tick_miss or 0
    slider_end_hits = statistics.slider_tail_hit or 0

    pp = recent[limit_number].pp
    if pp == None:
        pp = "0.00"
    else:
        pp = format(pp, ".2f")

    n300 = statistics.great
    n100 = statistics.ok
    n50 = statistics.meh
    miss = statistics.miss
    return accuracy, n300, n100, n50, miss, max_combo, mods, grade.value, pp, large_tick_hits, slider_end_hits, large_tick_miss

async def map_download(beatmap, on_download_start=None, on_download_fail=None):
    """
    Downloads the specified beatmap and extracts the required files.
    """
    try:
        os.mkdir("mapfolder")
    except FileExistsError:
        print(f"Directory already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create.")
    except Exception as e:
        print(f"An error occurred: {e}")

    manager = get_manager()
    main_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(main_path, "mapfolder")
    path = manager.get_file_path(beatmap[0])

    if not os.path.exists(path):
        manager.add_beatmap(beatmap[0])
        if on_download_start:
            await on_download_start()

        try:
            resp = requests.get(f'https://beatconnect.io/b/{beatmap[0]}', timeout=10)
            resp.raise_for_status()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            if on_download_fail:
                await on_download_fail()
            return

        with open(path, 'wb') as f:
            for buff in resp.iter_content(chunk_size=8192):
                f.write(buff)

    search_text = f'[{beatmap[1]}]'
    with zipfile.ZipFile(path, 'r') as zip_ref:
        matching_files = [file for file in zip_ref.namelist() if search_text in file]

        for file in matching_files:
            zip_ref.extract(file, folder_path)
            map_file = file

    manager.use_beatmap(beatmap[0])
    manager.save_state()
    beatmap_file = os.path.join(manager.base_directory, map_file)
    return beatmap_file

def mod_convert(mods):
    """
    Converts the mods list to a JSON string.
    """
    mods_dict = []
    for mod in mods:
        mod_dict = {"acronym": mod.acronym}
        if mod.settings:
            mod_dict["settings"] = mod.settings
        mods_dict.append(mod_dict)

    mods_json = json.dumps(mods_dict)
    return mods_json
