Intro to the Polympics API wrapper
==================================

Creating a client
-----------------

The first thing you need to do to use the API is create an API client. There are 3 types of client:

- Unauthenticated
- App-authenticated
- User-authenticated

Creating an unauthenticated client is very simple:

.. code-block:: python

   client = UnauthenticatedClient()

However, if you want to do anything other than read-only operations,
you'll need to authenticate. To use app credentials, see the following
example:

.. code-block:: python

   credentials = Credentials('A3', 'YOUR-TOKEN-HERE')
   client = AppClient(credentials)

Creating a user-authenticated client is very similar:

.. code-block:: python

   credentials = Credentials('A3', 'YOUR-TOKEN-HERE')
   client = UserClient(credentials)

.. note::

   All three clients take an additional parameter, ``base_url``. This is
   the location at which the API is hosted, for example
   ``http://127.0.0.1:8000`` or ``https://api.polytopia.fun``.

Getting an account
------------------

You can get an account by Discord ID using ``get_account``. For example:

.. code-block:: python

   account = client.get_account(12345678901234)
   print(account.display_name)
   print(account.permissions)
   print(account.team.name)

Getting a team
--------------

You can get a team by ID using ``get_team``. For example:

.. code-block:: python

   team = client.get_team(31)
   print(team.name)
   print(team.member_count)

Listing all accounts
--------------------

You can list all accounts using ``list_accounts``. For example:

.. code-block:: python

   async for account in client.list_accounts():
       print(account.display_name)

You can also get results a page at a time:

.. code-block:: python

   accounts = client.list_accounts()
   for account in await accounts.get_page(0):
       print(account.display_name)

You can use the ``search`` and ``team`` parameters to narrow down results.

.. code-block:: python

    print(f'Members from team {team.name} with "bob" in their name:')
    async for account in client.list_accounts('bob', team=team):
        print(account.display_name)

Listing all teams
-----------------

You can list all teams using ``list_teams``. For example:

.. code-block:: python

   async for team in client.list_teams():
       print(team.name)

This supports the same pagination system as ``list_accounts``, as well
as the ``search`` parameter:

.. code-block:: python

   teams = client.list_teams(search='foo')
   print([team.name for team in await teams.get_page(0)]

Creating an account
-------------------

Registering a user is a simple call to ``create_account``:

.. code-block:: python

   team = await client.get_team(5)
   account = await client.create_account(
       discord_id=1234567,
       display_name='Artemis',
       team=team
   )
   assert account.display_name == 'Artemis'
   assert account.team.id == 5

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission.

Editing an account
------------------

Editing a user's account can be done with ``update_account``:

.. code-block:: python

   account = await client.get_account(41129492792313)
   await client.update_account(account, display_name='Artemis')
   assert account.display_name == 'Artemis'

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission.

You can similarly update a user's team:

.. code-block:: python

   await client.update_account(account, team=team)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_teams`` permission, or just a ``UserClient``
   with the ``manage_own_team`` permission who is a member of the
   given team.

You can also update user permissions with the ``grant_permissions``
and ``revoke_permissions`` args, subject to the following rules:

- You must be authenticated.
- You cannot grant permissions you do not have.
- You cannot grant ``authenticate_users``, since that's not a permission users can have.
- You cannot grant permissions unless you have the ``manage_permissions`` permission, except as stated below:
- You *can* grant the ``manage_own_team`` permission to other members of your own team (as long as you also have ``manage_own_team``).

Example:

.. code-block::python

   await client.update_account(
       account, grant_permissions=Permissions(manage_own_team=True),
       revoke_permissions=Permissions(manage_teams=True)
   )

Deleting an account
-------------------

You can delete a user's account with the ``delete_account`` method:

.. code-block:: python

   account = await client.get_account(124214913289)
   await client.delete_account(account)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission.

Creating a team
---------------

You can create a team using the ``create_team`` method. It accepts one
parameter, ``name``, for the team's name:

.. code-block:: python

   team = await client.create_team('Gods of Olympus')
   assert team.name == 'Gods of Olympus'

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_teams`` permission.

Editing a team
--------------

You can edit a team using the ``update_team`` method. It accepts the same
``name`` parameter as ``create_team``:

.. code-block:: python

   team = await client.get_team(13)
   await client.update_team(team, name='Cool Kidz')
   assert team.name == 'Cool Kidz'

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_teams`` permission, or just a ``UserClient``
   with the ``manage_own_team`` permission who is a member of the
   given team.

Deleting a team
---------------

You can delete a team with the ``delete_team`` method. It accepts a single
argument, the team to delete:

.. code-block:: python

   team = await client.get_team(28)
   await client.delete_team(team)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_teams`` permission, or just a ``UserClient``
   with the ``manage_own_team`` permission who is a member of the
   given team.

Create a user auth session
--------------------------

An ``AppClient`` can create user sessions, which can in turn be used by a
``UserClient`` as authentication. More usefully, user session can be passed
to the frontend, so that the user they are for can manipulate the API
client-side. Since an attacker intercepting these credentials could
authenticate as the user, these have a short lifetime, by default 30 minutes.

Example:

.. code-block:: python

   account = await client.get_account(1318219824080)
   session = await client.create_session(account)
   print(session.expires_at)
   user_client = UserClient(session)

.. note::

   This requires an ``AppClient`` with the ``authenticate_users``
   permission.

Reset the client's token
------------------------

The token of an ``AppClient`` can be reset using ``reset_token``. Note that the
client *will* automatically update to use the new token. This function returns
an ``AppCredentials`` object, which can be used in place of credentials,
and also provides the attribute ``display_name``, which is the
human-readable name of the app.

.. code-block:: python

   await client.reset_token()

.. note::

   This requires an ``AppClient`` (you cannot reset a user token, since
   they are short-lived anyway).

Get the authenticated app
-------------------------

When authenticated with an ``AppClient``, you can use ``get_app`` to get
metadata on the authenticated app. Note that unlike ``reset_token``, this
does *not* return the app's new token.

.. code-block:: python

   app = await client.get_app()
   print(app.display_name)

.. note::

   This requires an ``AppClient``.

Getting the authenticated user
------------------------------

A ``UserClient`` can get the account of the user it has authenticated as
using the ``get_self`` method:

.. code-block:: python

   account = await client.get_self()
   print(account.display_name)

.. note::

   This requires a ``UserClient``, since an ``AppClient`` has no associated
   user.

Errors
------

If the API returns an error, the wrapper will raise a ``PolympicsError``.
This has the attributes ``code`` (the HTTP status code that was used, eg.
``404`` or ``500``) and ``detail`` (a human-readable message indicating what
went wrong).
