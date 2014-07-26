#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import run, put, local, cd, lcd, sudo, settings
from fabric.contrib import files
import os

TMP_PATH     = '/tmp/deploy_tmp'
GIT_URL      = 'git@github.com'
REPO         = ''
PRODUCT      = ''
PRODUCT_ROOT = ''
DEPLOY_USER  = 'root'
VERSION_DIR  = 'versions'


def is_valid_path(path, is_link=False):
    with settings(warn_only=True):
        if files.exists(path) and (not is_link or files.is_link(path)):
            return True
        return False


def switch_version(product_path, product_root, version):
    link_from = os.path.join(product_root, VERSION_DIR, version)
    if is_valid_path(product_path, is_link=True):
        sudo('rm -v %s' % product_path.rstrip('/'))
    sudo('ln -svf %s %s' % (link_from, product_path))


def deploy(product,product_root,repo,tag,user):
    deploy_path = os.path.join(product_root, VERSION_DIR)
    sudo('mkdir -pv %s' % deploy_path, user=user)
    if not is_valid_path(deploy_path):
        print "[ERROR] could not create %s." % deploy_path
        raise

    # git url
    url = GIT_URL + ':' + repo + '/' + product.lower() + '.git'
    clone_path = os.path.join(TMP_PATH, product)
    local('mkdir -pv %s' % TMP_PATH)
    try:
        local('git clone %s %s' % (url, clone_path))
        with lcd(clone_path):
            if tag == '':
                tag = local('git for-each-ref --sort=taggerdate | tail -1 \
                             | sed -e "s/.*refs\/tags\///g"', capture=True)
            local('git checkout -b %s' % tag)
        with lcd(TMP_PATH):
            local('mv -v %s %s' % (product, tag))
            local('tar czvf %s.tar.gz %s --exclude-vcs' % (tag, tag))
        local_path = TMP_PATH + '/' + tag + '.tar.gz'
        put(local_path, deploy_path, use_sudo=True)
        with cd(deploy_path):
            run('pwd')
            tar_file = tag + '.tar.gz'
            sudo('tar zxvf %s' % tar_file)
            sudo('chown %s %s' % (user, tag))
            sudo('rm %s' % tar_file)

    except:
        print "[ERROR] %s could not be deployed." % product
        exit(1)
    finally:
        local('rm -rf %s' % TMP_PATH)


def release(product=PRODUCT, product_root=PRODUCT_ROOT, repo=REPO, tag='', user=DEPLOY_USER):
    sudo('hostname && whoami', user=user)
    deploy(product,product_root,repo,tag,user)

    product_path = os.path.join(product_root, product)
    switch_version(product_path, product_root, tag)
    if not is_valid_path(product_path, is_link=True):
        print "[ERROR] %s was deployed, but could not be created symbolic link." % product
        exit(1)
