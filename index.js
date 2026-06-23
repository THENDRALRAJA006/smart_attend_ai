import { withSupabase } from "@supabase/server"

/**
 * Health check & initialization endpoint.
 * Uses auth: "none" to verify public connectivity to PostgreSQL database.
 */
export default {
  fetch: withSupabase({ auth: "none" }, async (req, ctx) => {
    try {
      const { data, error } = await ctx.supabaseAdmin
        .from("students")
        .select("id, full_name, roll_number")
        .limit(5);

      if (error) {
        return new Response(JSON.stringify({ status: "error", message: error.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }

      return new Response(
        JSON.stringify({
          status: "ok",
          message: "Supabase Connection verified successfully!",
          sample_students: data
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      );
    } catch (err) {
      return new Response(JSON.stringify({ status: "error", message: err.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
  }),
}

/**
 * RLS-scoped handler to query a user's attendance records.
 * Uses auth: "user" to enforce JWT verification via SUPABASE_JWKS_URL.
 */
export const getStudentAttendance = withSupabase({ auth: "user" }, async (req, ctx) => {
  try {
    const url = new URL(req.url);
    const studentId = url.searchParams.get("student_id");

    if (!studentId) {
      return new Response(JSON.stringify({ error: "Missing student_id parameter" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

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
});
