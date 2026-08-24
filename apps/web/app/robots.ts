import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/about", "/ask", "/discord/privacy", "/discord/terms"],
        disallow: [
          "/activity",
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
