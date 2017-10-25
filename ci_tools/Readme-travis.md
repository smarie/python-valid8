This is a reminder on how to grant travis the rights to deploy your site on github pages, python package to pypi and release files to github

# PREREQUISITE 

## Get access to a linux machine

The following does not work on windows as explained [here](https://github.com/travis-ci/travis-ci/issues/4746)

## Install travis commandline 

You have to be outside of the proxy for everything to work correctly, otherwise you will get strange errors mentioning ipaddr... either here or later in the process.

Install ruby using RVM : (**DO NOT USE su OR sudo**)  

```bash
> \curl -sSL https://get.rvm.io | bash -s stable --ruby
> source /home/ubuntu/.rvm/scripts/rvm
> rvm install ruby (this installs to /home/ubuntu/.rvm/src/ruby...)
```

Then install travis commandline:

```bash
> gem install travis
```

source: 
 * http://railsapps.github.io/installrubyonrails-ubuntu.html
 * http://sirupsen.com/get-started-right-with-rvm/
	

## Optional: setup a shared folder between your development machine and the linux machine 

If possible the shared folder should be the git folder, so that travis automatically detects the git project.


# Generating the access keys for travis

## To deploy a site on gh-pages using `mkdocs gh-deploy` (or for any `git push` operation)

Generate an asymetric security key (public + private):

 * On windows: open git bash (not windows cmd)
 * Execute the following but **DO NOT provide any passphrase when prompted (simply press <enter>)**

```bash
ssh-keygen -t rsa -b 4096 -C "<your_github_email_address>" -f ci_tools/github_travis_rsa
```

On the github repository page, `Settings > Deploy Keys > Add deploy key > add` the PUBLIC generated key (the file `ci_tools/github_travis_rsa.pub`)


Use travis CLI to encrypt your PRIVATE key:

```bash
> cd to the shared folder (/media/...)
> source /home/ubuntu/.rvm/scripts/rvm
> travis login
> travis encrypt-file -r <git-username>/<repo-name> ci_tools/github_travis_rsa   (DO NOT USE --add option since it will remove all comments in your travis.yml file!)
```

Follow the instructions on screen :
- copy the line starting with `openssl ...` to your `travis.yml` file. 
- modify the relative path to the generated file by adding 'ci_tools/' in front of 'github_travis_rsa_...enc'.
- git add the generated file 'github_travis_rsa_...enc' but DO NOT ADD the private key

source: 
   * https://djw8605.github.io/2017/02/08/deploying-docs-on-github-with-travisci/ (rejecting https://docs.travis-ci.com/user/deployment/pages/ as this would grant full access to travis)
   * https://docs.travis-ci.com/user/encrypting-files/ 
   * https://gist.github.com/domenic/ec8b0fc8ab45f39403dd

## To deploy python wheels on PyPi

Similar procedure to encrypt the PyPi password for deployments:

```bash
> (cd, source, travis login)
> travis encrypt -r <git-username>/<repo-name> <pypi_password>
```
Copy the resulting string in the `travis.yml` file under deploy > provider: pypi > password > secure

source: https://docs.travis-ci.com/user/deployment/pypi/


## To deploy file releases on github

Similar procedure to encrypt the OAuth password for github releases. **WARNING** unlike 'travis encrypt', this WILL modify your `travis.yml` file. Therefore you should make a backup of it beforehand, and then execute this command with the '--force' option.

```bash
> (cd, source, travis login)
> travis login
> travis setup releases
```

Copy the string in the `travis.yml` file under deploy > provider: releases > api-key > secure

source: https://docs.travis-ci.com/user/deployment/releases/