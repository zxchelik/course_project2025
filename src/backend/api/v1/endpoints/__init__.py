from api.v1.endpoints import auth, user, role, inventory, stats, personal_stats, report

routers = [auth.router, user.router, role.router, inventory.router, stats.router, personal_stats.router, report.router]
