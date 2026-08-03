from unittest.mock import Mock

import aiohttp.client_reqrep

_original_init = aiohttp.client_reqrep.ClientResponse.__init__


def _patched_init(self, method, url, *, writer, continue100, timer, request_info,
                  traces, loop, session, stream_writer=None):
    if stream_writer is None:
        stream_writer = Mock()
    return _original_init(self, method, url, writer=writer, continue100=continue100,
                          timer=timer, request_info=request_info, traces=traces,
                          loop=loop, session=session, stream_writer=stream_writer)


aiohttp.client_reqrep.ClientResponse.__init__ = _patched_init
