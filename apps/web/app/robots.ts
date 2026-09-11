import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/about", "/discord/privacy", "/discord/terms"],
        disallow: [
          "/activity",
          "/ask",
          "/conversations",
          "/discord",
          "/evaluation",
          "/knowledge",
          "/settings",
          "/sources",
          "/training",
          "/api",
        ],
      },
    ],
  };
}
