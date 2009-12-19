#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast, UserProfile, Episode, Device, EpisodeAction, SubscriptionAction, ToplistEntry, Subscription
from mygpo.web.forms import UserAccountForm
from mygpo.api.opml import Exporter
from django.utils.translation import ugettext as _

def home(request):
       if request.user.is_authenticated():
              subscriptionlist = create_subscriptionlist(request)              

              return render_to_response('home-user.html', {
                    'subscriptionlist': subscriptionlist
              }, context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

def create_subscriptionlist(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    l = {}
    for s in subscriptions:
        if s.podcast in l:
            l[s.podcast]['devices'].append(s.device.name)
        else:
            e = Episode.objects.filter(podcast=s.podcast).order_by('-timestamp')
            episode = e[0] if e.count() > 0 else None
            devices = [s.device.name]
            l[s.podcast] = {'podcast': s.podcast, 'episode': episode, 'devices': devices}

    return l.values()


def create_subscriptionhistory(request, pid): 
    podcastname = Podcast.objects.filter(id=pid).values_list('title', flat=True)
    sublog = SubscriptionAction.objects.filter(podcast__id = pid).order_by('-timestamp')
    subscriptionhistorylist = [{'timestamp': s.timestamp.strftime('%d.%m.%Y %H:%M'), 'device_id': s.device_id, 'action': s.action} for s in sublog]
    for index, entry in enumerate(subscriptionhistorylist):
        dev = Device.objects.filter(id=subscriptionhistorylist[index]['device_id']).values_list('name', flat=True)
        subscriptionhistorylist[index]['device'] = ''
            
        for i, d in enumerate(dev):
            if i == 0:
               subscriptionhistorylist [index]['device'] += d
            else:
               subscriptionhistorylist [index]['device'] += ", "  + d 

    return render_to_response('subscriptionhistory.html', {
                    'subscriptionhistorylist': subscriptionhistorylist,
                    'podcastname': podcastname[0]
              }, context_instance=RequestContext(request))


def account(request):
    success = False

    if request.method == 'POST':
        form = UserAccountForm(request.POST)

        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.save()
            request.user.get_profile().public_profile = form.cleaned_data['public']
            request.user.get_profile().save()

            success = True

    else:
        form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.get_profile().public_profile
            })

    return render_to_response('account.html', {
        'form': form,
        'success': success
    }, context_instance=RequestContext(request))

def toplist(request):
    len = 30
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:len]
    return render_to_response('toplist.html', {
        'count'  : len,
        'entries': entries,
    }, context_instance=RequestContext(request))


def toplist_opml(request, count):
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:count]
    exporter = Exporter(_('my.gpodder.org - Top %s') % count)

    opml = exporter.generate([e.podcast for e in entries])

    return HttpResponse(opml, mimetype='text/xml')
 


