5.0
===

Moved ``http API`` to `pmxbot.webhooks
<https://pypi.org/project/pmxbot.webhooks>`_.

4.0.1
=====

#3: Use ``cherrypy.engine.exit`` for cleaner exit of the webhooks.

4.0
===

Removed Kiln and Bitbucket hooks. As YouGov is no longer using
these services, it's unlikely that anyone will need this code.
It's there in the history if you want it.

3.16.1
======

Fixed usage of Twilio Client, unmentioned in the migration guide.

3.16
====

Fixed error where ``twilio.rest.TwilioRestClient`` was renamed
to ``twilio.rest.Client`` (better name, to be sure) in v6 of the
library. Reviewed the `migration guide
<https://www.twilio.com/docs/libraries/python/migration-guide>`_
and found no other relevant changes.

3.15
====

Limit commit reports to 10.

Use inflect for easier nice name rendering(s).

No longer show branches for Kiln commits and only show tags.

3.14
====

(semver deviation - should have been +0.0.1)

Fix commit's branch name

3.13
====

Show branches and tags for Kiln commits.

3.12
====

HTTP integration now reports more detail when a message is
received.

Refreshed project packaging.

3.11
====

Also log Close events from Fogbugz.

3.10
====

#2: Filter build statuses.

3.9
===

Handle more VR events.

3.8
===

Moved project hosting to Github.

3.7
===

Support for newer Jenkins Notification plugin wording.

3.6
===

Added support for Bitbucket webhooks.

3.0
===

Kiln and BitBucket now also use the ChannelSelector. Therefore, clients
should be updated not to pass the channel, and instead just specify the
endpoint (i.e. http://my.pmxbot/kiln or /bitbucket). Furthermore, the channel
routing should be specified in the config based on the repository name.

2.0
===

FogBugz config key should now be "FogBugz channels".

Jenkins HTTP endpoint now uses config to route messages to channels rather
than requiring it in the URL. The new endpoint is simply "/jenkins".
