"""Shared helpers: load project.json and resolve paths inside the repo."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    path = os.environ.get('PROJECT', os.path.join(ROOT, 'project.json'))
    cfg = json.load(open(path))
    cfg['_root'] = ROOT
    cfg['_path'] = path
    cfg['_work'] = os.path.join(ROOT, cfg.get('work', 'work'))
    os.makedirs(cfg['_work'], exist_ok=True)
    return cfg


def wpath(cfg, *parts):
    """a path inside the work folder"""
    return os.path.join(cfg['_work'], *parts)


def rpath(cfg, p):
    """a path relative to the repo root (absolute paths pass through)"""
    return p if os.path.isabs(p) else os.path.join(ROOT, p)
