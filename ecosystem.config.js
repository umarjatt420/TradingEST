module.exports = {
  apps: [
    {
      name: "tradingest",
      script: "/home/ubuntu/TradingEST/estvenv/bin/python",
      args: "manage.py runserver 0.0.0.0:3001",
      cwd: "/home/ubuntu/TradingEST",
      interpreter: "none",
      autorestart: true,
      watch: false,
    }
  ]
}
