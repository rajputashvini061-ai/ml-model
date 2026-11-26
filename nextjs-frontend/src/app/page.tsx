import CourseRecommender, { type MetaPayload } from "@/components/CourseRecommender";
import metaData from "@/data/meta.json";

export const dynamic = "force-static";

export default function HomePage() {
  return <CourseRecommender initialMeta={metaData as MetaPayload} />;
}
