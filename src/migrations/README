# Alembic main commands

All commands should be run after spinning the containers using

```shell
docker compose up -d db backend
```

## Create a revision

Alembic allows you to record migration operation using DB operations. Let's create a revision file:

```shell
docker compose exec -T backend alembic revision --autogenerate
```

Once generated, you should edit the revision file in src/migrations/versions that was created. See example [here](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async/blob/main/fastapi-alembic-sqlmodel-async/alembic/versions/2022-09-25-19-46_60d49bf413b8.py).

## Apply revisions

Now apply all the revisions

```shell
docker compose exec backend alembic upgrade head
```
