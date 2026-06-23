import { withSupabase } from "@supabase/server"

/**
 * Supabase Edge Function request handler for querying attendance records.
 * Uses auth: "user" to enforce user JWT validation.
 */
export default {
  fetch: withSupabase({ auth: "user" }, async (req, ctx) => {
    try {
      const url = new URL(req.url);
      const studentId = url.searchParams.get("student_id");

      if (!studentId) {
        return new Response(JSON.stringify({ error: "Missing student_id parameter" }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      // RLS is automatically applied using the user's JWT context (ctx.supabase)
      const { data, error } = await ctx.supabase
        .from("attendance")
        .select("*")
        .eq("student_id", studentId)
        .order("timestamp", { ascending: false });

      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }

      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
}
