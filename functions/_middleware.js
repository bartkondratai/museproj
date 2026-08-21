// Hostname-based routing: beartandmusic.pl serves public pages,
// in.beartandmusic.pl serves internal/staff-only pages.
// Cloudflare Access should be configured on in.beartandmusic.pl in the
// Cloudflare dashboard to gate these paths — this middleware only routes.

const INTERNAL_HOST = 'in.beartandmusic.pl';
const PUBLIC_HOST = 'beartandmusic.pl';

const INTERNAL_PREFIXES = [
  '/residents',
  '/associates',
  '/spaces/admin',
  '/clauded',
  '/directory',
  '/login',
  '/systeminfo',
  '/intranet',
];

function isInternalPath(pathname) {
  return INTERNAL_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);
  const isInternalHost = url.hostname === INTERNAL_HOST;
  const internalPath = isInternalPath(url.pathname);

  // in.beartandmusic.pl/ -> intranet home, served in place (no URL change)
  if (isInternalHost && url.pathname === '/') {
    const rewritten = new URL(request.url);
    rewritten.pathname = '/intranet/';
    return next(new Request(rewritten, request));
  }

  // Internal pages requested on the public host -> send to the intranet subdomain
  if (internalPath && !isInternalHost) {
    url.hostname = INTERNAL_HOST;
    return Response.redirect(url.toString(), 301);
  }

  // Public pages requested on the intranet subdomain -> send to the public domain
  if (!internalPath && isInternalHost) {
    url.hostname = PUBLIC_HOST;
    return Response.redirect(url.toString(), 301);
  }

  return next();
}
