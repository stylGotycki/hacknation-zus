/**
 * Route table: English route name -> public (Polish) URL.
 *
 * - The key is the English route: it is the folder name in `src/app/<key>/`.
 * - The value is the URL users see in the address bar and that every <Link> must use.
 * - nginx serves the public URL from the English route and redirects the English URL to the
 *   public one (see `infra/nginx/default.conf`). Keep both tables identical:
 *   `make check-routes` fails when they differ.
 */
export const PUBLIC_PATHS = {
  calculator: "/kalkulator",
  timeline: "/os-czasu",
  account: "/moje-swiadczenia",
  applications: "/wnioski",
  zus: "/dane-zus",
  help: "/pomoc",
  login: "/logowanie",
  admin: "/admin",
} as const;

export type RouteName = keyof typeof PUBLIC_PATHS;

const startsWithSegment = (pathname: string, base: string) =>
  pathname === base || pathname.startsWith(`${base}/`);

/**
 * Is `pathname` inside the given route? Accepts both forms: the browser reports the public
 * URL, while server rendering sees the English one (nginx rewrites it before Next.js).
 */
export function isRouteActive(pathname: string, route: RouteName): boolean {
  return (
    startsWithSegment(pathname, PUBLIC_PATHS[route]) ||
    startsWithSegment(pathname, `/${route}`)
  );
}
