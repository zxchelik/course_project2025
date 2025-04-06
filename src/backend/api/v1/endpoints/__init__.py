from src.backend.api.v1.endpoints import auth, user, role, inventory, stats

routers = [auth.router, user.router, role.router, inventory.router, stats.router]
