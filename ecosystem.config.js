module.exports = {
  apps : [{
    name: 'worker',
    cmd: 'main.pyw',
    interpreter: 'python3',
  }],

  deploy : {
    production : {
      user : 'gp',
      host : ['119.28.137.13'],
      ref  : 'origin/main',
      repo : 'git@github.com:genru/DouyinLiveRecorder.git',
      path : '/home/gp/monday-worker',
      'pre-deploy-local': '',
      'post-deploy' : 'pip3 install -r requirements.txt && pm2 reload ecosystem.config.js --env production'
    }
  }
};
