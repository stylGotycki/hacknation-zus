import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { GuideFrame } from "@/components/zus/guide-frame";

/** The parent's guide: zus.pl-like header, side navigation and footer. */
export default function GuideLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <GuideFrame>{children}</GuideFrame>
      <SiteFooter />
    </>
  );
}
