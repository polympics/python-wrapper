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

   credentials = Credentials('S3', 'YOUR-TOKEN-HERE')
   client = UserClient(credentials)

.. note::

   All three clients take an additional parameter, ``base_url``. This is
   the location at which the API is hosted, for example
   ``http://127.0.0.1:8000`` or ``https://api.polytopia.fun``.

Getting an account
------------------

You can get an account by Discord ID using ``get_account``. For example:

.. code-block:: python

   account = await client.get_account(12345678901234)
   print(account.name)
   print(account.permissions)
   print(account.team.name)

Getting a team
--------------

You can get a team by ID using ``get_team``. For example:

.. code-block:: python

   team = await client.get_team(31)
   print(team.name)
   print(team.member_count)

Getting an award
----------------

You can get an award by ID using the ``get_award`` method. For example:

.. code-block:: python

   award = await client.get_award(42)
   print(award.title, award.image_url)
   for awardee in award.awardees:
       # awardee is an Account object.
       print(awardee.name)

Listing all accounts
--------------------

You can list all accounts using ``list_accounts``. For example:

.. code-block:: python

   async for account in client.list_accounts():
       print(account.name)

You can also get results a page at a time:

.. code-block:: python

   accounts = client.list_accounts()
   for account in await accounts.get_page(0):
       print(account.name)

You can use the ``search`` and ``team`` parameters to narrow down results.

.. code-block:: python

   print(f'Members from team {team.name} with "bob" in their name:')
   async for account in client.list_accounts('bob', team=team):
       print(account.name)

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
   print([team.name for team in await teams.get_page(0)])

Checking if signups are open
----------------------------

Call ``check_signups`` on any client to check if signups are open:

.. code-block:: python

   if await client.check_signups():
       print('Signups are open.')
   else:
       print('Signups are closed.)

New users will not be allowed to register when signups are closed.

Creating an account
-------------------

Registering a user is a simple call to ``create_account``:

.. code-block:: python

   team = await client.get_team(5)
   account = await client.create_account(
       id=1234567,
       name='Artemis',
       discriminator='8472',
       avatar_url='https://picsum.photos/200',
       team=team
   )
   assert account.name == 'Artemis'
   assert account.team.id == 5

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission.

You can also chose the permissions to grant the user:

.. code-block:: python

   account = await client.create_account(
       id=1234567,
       name='Artemis',
       discriminator='8472',
       team=team,
       permissions=Permissions(
           manage_teams=True, manage_account_details=True
       )
   )

.. note::

   In order to grant permissions to a user:

   - You must be authenticated.
   - You cannot grant permissions you do not have.
   - You cannot grant ``authenticate_users``, since that's not a permission users can have.
   - You cannot grant permissions unless you have the ``manage_permissions`` permission, except as stated below:
   - You *can* grant the ``manage_own_team`` permission to other members of your own team (as long as you also have ``manage_own_team``).

Editing an account
------------------

Editing a user's account can be done with ``update_account``:

.. code-block:: python

   account = await client.get_account(41129492792313)
   account = await client.update_account(
      account, name='Artemis', discriminator='1231'
   )
   assert account.name == 'Artemis'

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission.

You can similarly update a user's team:

.. code-block:: python

   account = await client.update_account(account, team=team)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_teams`` permission, or a ``UserClient`` authenticated
   with the given account.

Or you can remove a user from a team, using the ``NO_TEAM`` constant:

.. code-block:: python

   account = await client.update_account(account, team=polympics.NO_TEAM)

.. note::

   This requires permissions as explained above for adding a user to a team,
   with the addition that you can remove a user from a team if you are a member
   of that team and have the ``manage_own_team`` permission.

You can also update user permissions with the ``grant_permissions``
and ``revoke_permissions`` args, subject to the rules outlined in
"Creating an account".

Example:

.. code-block:: python

   account = await client.update_account(
       account, grant_permissions=Permissions(manage_own_team=True),
       revoke_permissions=Permissions(manage_teams=True)
   )

Using the ``discord_token`` parameter, you can update a user's name,
discriminator and avatar URL to match Discord. This requires no permissions,
since user tokens can be authenticated with Discord.

Example:

.. code-block:: python

   account = await client.update_account(account, discord_token=token)

Deleting an account
-------------------

You can delete a user's account with the ``delete_account`` method:

.. code-block:: python

   account = await client.get_account(124214913289)
   await client.delete_account(account)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_account_details`` permission, or just a ``UserClient`` associated
   with the given account.

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
   team = await client.update_team(team, name='Cool Kidz')
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

Creating an award
-----------------

You can create an award with the ``create_award`` method:

.. code-block:: python

   account_1 = await client.get_account(508140149014901)
   team = await client.get_team(123)
   award = await client.create_award(
       title='Perfect 10 Gold',
       image_url='https://link.to/icon.png',
       team=team,
       accounts=[account_1]
   )
   print(award.id, award.title)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_awards`` permission.

Editing an award
----------------

You can edit an award with the ``update_award`` method:

.. code-block:: python

   award = await client.get_award(12)
   award = await client.update_award(award, title='Gold - Perfect 10')

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_awards`` permission.

Deleting an award
-----------------

You can delete an award with the ``delete_award`` method:

.. code-block:: python

   award = await client.get_award(52)
   await client.delete_award(award)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_awards`` permission.

Giving an award to a user
-------------------------

You can give a user an existing award with the ``give_award`` method:

.. code-block:: python

   account = await client.get_account(130914109419411)
   award = await client.get_award(19)
   await client.give_award(award, account)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_awards`` permission.

Taking an award from a user
---------------------------

You can take an award away from a user that has it with the ``take_award`` method:

.. code-block:: python

   account = await client.get_account(8713710931790741)
   award = await client.get_award(13)
   await client.take_award(award, account)

.. note::

   This requires an ``AppClient`` or ``UserClient`` with the
   ``manage_awards`` permission.

Registering a callback
----------------------

You can register an HTTP callback for a specific event type (currently only ``account_team_update``) using the ``create_callback`` method.

.. code-block:: python

   await client.create_callback(
       event=EventType.account_team_update,
       url='https://example.com/fake_callback',
       secret='obviously-dont-use-this'
   )

.. note::

   This requires an ``AppClient``. It will overwrite any existing callback for this event type.

Listing all callbacks
---------------------

You can list all callbacks registered for your app using the ``get_callbacks`` method:

.. code-block:: python

   callbacks = await client.get_callbacks()
   for event, cb_url in callbacks.items():
       print(f'{cb_url} registered for {event.value}')

.. note::

   This requires an ``AppClient``.

Getting a specific callback
---------------------------

You can get information on a specific callback using the ``get_callback`` method:

.. code-block:: python

   callback = await client.get_callback(EventType.account_team_update)
   print(callback.id)
   print(callback.event.value)
   print(callback.url)

.. note::

   This requires an ``AppClient``.

Deleting a callback
-------------------

You can delete the callback for a specific event type using the ``delete_callback`` method:

.. code-block:: python

   await client.delete_callback(EventType.account_team_update)

.. note::

   This requires an ``AppClient``.

Handling a callback event
-------------------------

This library does not implement an HTTP server to listen for events, so you will have to implement that yourself. Once you recieve an event, you should make sure that the ``Authorization`` header is equal to ``Bearer <secret>``, where ``<secret>`` is the secret you passed to ``create_callback``.

Once you have recieved and validated an event, you can use a handler function to parse the data. The following handler functions are available:

- ``account_team_update``

Creating a user auth session
----------------------------

An ``AppClient`` can create user sessions, which can in turn be used by a
``UserClient`` as authentication. More usefully, user session can be passed
to the frontend, so that the user they are for can manipulate the API
client-side.

Example:

.. code-block:: python

   account = await client.get_account(1318219824080)
   session = await client.create_session(account)
   print(session.expires_at)
   user_client = UserClient(session)

.. note::

   This requires an ``AppClient`` with the ``authenticate_users``
   permission.

Authenticating via Discord OAuth2
---------------------------------

Alternatively, you can use a Discord user authentication token to create a
user session (these can be obtained using Discord OAuth2, which is beyond the
scope of this library). This has the advantage that you do not need to be
otherwise authenticated, so it can be used on the frontend (eg. with the OAuth2
implicit grant flow).

Example:

.. code-block:: python

   session = await client.discord_authenticate(token)
   user_client = UserClient(session)

Note that the token used must be authorised for the ``identify`` scope.

Resetting the client's token
----------------------------

The token of an ``AppClient`` or ``UserClient`` can be reset using
``reset_token``. Note that the client *will* automatically update to use the
new token. This function returns an ``AppCredentials`` object for an
``AppClient``, or a ``Session`` object for a ``UserClient``, either of which
can be used in place of credentials, and also provide some metadata.

.. code-block:: python

   await client.reset_token()

.. note::

   This requires an ``AppClient`` or ``UserClient``.

Getting the authenticated app
-----------------------------

When authenticated with an ``AppClient``, you can use ``get_self`` to get
metadata on the authenticated app. Note that unlike ``reset_token``, this
does *not* return the app's new token.

.. code-block:: python

   app = await client.get_self()
   print(app.name)

Getting the authenticated user
------------------------------

A ``UserClient`` can get the account of the user it has authenticated as
using the same method:

.. code-block:: python

   account = await client.get_self()
   print(account.name)

Closing the connection
----------------------

Before exiting, your app should call the ``close`` method of any clients you
have opened:

.. code-block:: python

   await client.close()

Errors
------

If the API returns an error, the wrapper will raise a ``PolympicsError``.
This has the ``code`` attribute (the HTTP status code that was used, eg.
``404`` or ``500``).

There are also the following subclasses:

- ``ServerError`` indicates a server-side issue that it may be beyond the
  client's capability to resolve.
- ``DataError`` indicates an issue in the parameters passed to the API. This
  could indicate an issue in the library, but it will also be raised when a
  resource is not found. The ``issues`` attribute gives more detail, which can
  also be seen in the string representation of the error.
- ``ClientError`` indicates a client-side issue not covered by ``DataError``.
  The ``detail`` attribute gives more information, in a human-readable format.
