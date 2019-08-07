import os
import os.path as osp
import pytest
import tarfile
from testpath import assert_isdir, assert_isfile
import zipfile

from flit_core import build_thyself

@pytest.fixture()
def cwd_project():
    proj_dir = osp.dirname(osp.dirname(osp.abspath(build_thyself.__file__)))
    if not osp.isfile(osp.join(proj_dir, 'pyproject.toml')):
        pytest.skip("need flit_core source directory")

    old_cwd = os.getcwd()
    try:
        os.chdir(proj_dir)
        yield
    finally:
        os.chdir(old_cwd)


def test_prepare_metadata(tmp_path):
    dist_info = build_thyself.prepare_metadata_for_build_wheel(str(tmp_path))

    assert dist_info.endswith('.dist-info')
    assert dist_info.startswith('flit_core')
    dist_info = tmp_path / dist_info
    assert_isdir(dist_info)

    assert_isfile(dist_info / 'WHEEL')
    assert_isfile(dist_info, 'METADATA')


def test_wheel(tmp_path, cwd_project):
    filename = build_thyself.build_wheel(tmp_path)

    assert filename.endswith('.whl')
    assert filename.startswith('flit_core')
    path = tmp_path / filename
    assert_isfile(path)
    assert zipfile.is_zipfile(str(path))


def test_sdist(tmp_path, cwd_project):
    filename = build_thyself.build_sdist(tmp_path)

    assert filename.endswith('.tar.gz')
    assert filename.startswith('flit_core')
    path = tmp_path / filename
    assert_isfile(path)
    assert tarfile.is_tarfile(str(path))
