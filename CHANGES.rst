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