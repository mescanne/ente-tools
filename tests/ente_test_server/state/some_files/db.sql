--
-- PostgreSQL database dump
--

-- Dumped from database version 15.10 (Debian 15.10-1.pgdg120+1)
-- Dumped by pg_dump version 15.10 (Debian 15.10-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: app; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.app AS ENUM (
    'photos',
    'auth',
    'locker'
);


ALTER TYPE public.app OWNER TO pguser;

--
-- Name: model; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.model AS ENUM (
    'ggml-clip',
    'onnx-clip',
    'file-ml-clip-face',
    'derived'
);


ALTER TYPE public.model OWNER TO pguser;

--
-- Name: object_type; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.object_type AS ENUM (
    'file',
    'thumbnail',
    'mldata',
    'vid_preview',
    'img_preview'
);


ALTER TYPE public.object_type OWNER TO pguser;

--
-- Name: role_enum; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.role_enum AS ENUM (
    'VIEWER',
    'COLLABORATOR',
    'OWNER'
);


ALTER TYPE public.role_enum OWNER TO pguser;

--
-- Name: s3region; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.s3region AS ENUM (
    'b2-eu-cen',
    'scw-eu-fr',
    'scw-eu-fr-locked',
    'wasabi-eu-central-2',
    'wasabi-eu-central-2-v3',
    'scw-eu-fr-v3',
    'wasabi-eu-central-2-derived',
    'b5',
    'b6'
);


ALTER TYPE public.s3region OWNER TO pguser;

--
-- Name: stage_enum; Type: TYPE; Schema: public; Owner: pguser
--

CREATE TYPE public.stage_enum AS ENUM (
    'scheduled',
    'collection',
    'trash',
    'storage',
    'completed'
);


ALTER TYPE public.stage_enum OWNER TO pguser;

--
-- Name: ensure_no_common_entries(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.ensure_no_common_entries() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    all_buckets       s3region[];
    duplicate_buckets s3region[];
BEGIN
    -- Combine all bucket IDs into a single array
    all_buckets := ARRAY [NEW.latest_bucket] || NEW.replicated_buckets || NEW.delete_from_buckets ||
                   NEW.inflight_rep_buckets;

    -- Find duplicate bucket IDs
    SELECT ARRAY_AGG(DISTINCT bucket)
    INTO duplicate_buckets
    FROM unnest(all_buckets) bucket
    GROUP BY bucket
    HAVING COUNT(*) > 1;

    -- If duplicates exist, raise an exception with details
    IF ARRAY_LENGTH(duplicate_buckets, 1) > 0 THEN
        RAISE EXCEPTION 'Duplicate bucket IDs found: %. Latest: %, Replicated: %, To Delete: %, Inflight: %',
            duplicate_buckets, NEW.latest_bucket, NEW.replicated_buckets, NEW.delete_from_buckets, NEW.inflight_rep_buckets;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.ensure_no_common_entries() OWNER TO pguser;

--
-- Name: fn_update_authenticator_key_updated_at_via_updated_at(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.fn_update_authenticator_key_updated_at_via_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    --
    IF  (TG_OP = 'UPDATE' OR TG_OP = 'INSERT') THEN
        UPDATE authenticator_key SET updated_at = NEW.updated_at where user_id = new.user_id and
                updated_at < New.updated_at;
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.fn_update_authenticator_key_updated_at_via_updated_at() OWNER TO pguser;

--
-- Name: fn_update_collections_updation_time_using_update_at(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.fn_update_collections_updation_time_using_update_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    --
    IF  (TG_OP = 'UPDATE' OR TG_OP = 'INSERT') THEN
        UPDATE collections SET updation_time = NEW.updated_at where collection_id = new.collection_id and
                updation_time < New.updated_at;
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.fn_update_collections_updation_time_using_update_at() OWNER TO pguser;

--
-- Name: fn_update_entity_key_updated_at_via_updated_at(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.fn_update_entity_key_updated_at_via_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    --
    IF (TG_OP = 'UPDATE' OR TG_OP = 'INSERT') THEN
        UPDATE entity_key
        SET updated_at = NEW.updated_at
        where user_id = new.user_id
          and type = new.type
          and updated_at < New.updated_at;
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.fn_update_entity_key_updated_at_via_updated_at() OWNER TO pguser;

--
-- Name: now_utc_micro_seconds(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.now_utc_micro_seconds() RETURNS bigint
    LANGUAGE sql
    AS $$
SELECT CAST(extract(EPOCH from now() at time zone 'utc') * 1000000 as BIGINT) ;
$$;


ALTER FUNCTION public.now_utc_micro_seconds() OWNER TO pguser;

--
-- Name: th(bigint); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.th(epochtimeinmircoseconds bigint) RETURNS timestamp with time zone
    LANGUAGE plpgsql
    AS $$
begin
   return to_timestamp(cast(epochTimeinMircoSeconds/1000000 as bigint));
end;
$$;


ALTER FUNCTION public.th(epochtimeinmircoseconds bigint) OWNER TO pguser;

--
-- Name: trigger_updated_at_microseconds_column(); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION public.trigger_updated_at_microseconds_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.updated_at >= NEW.updated_at THEN
        NEW.updated_at = now_utc_micro_seconds();
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trigger_updated_at_microseconds_column() OWNER TO pguser;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: authenticator_entity; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.authenticator_entity (
    id uuid NOT NULL,
    user_id bigint NOT NULL,
    encrypted_data text,
    header text,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    is_deleted boolean DEFAULT false,
    CONSTRAINT authenticator_entity_state_constraint CHECK ((((is_deleted IS TRUE) AND (encrypted_data IS NULL)) OR ((is_deleted IS FALSE) AND (encrypted_data IS NOT NULL))))
);


ALTER TABLE public.authenticator_entity OWNER TO pguser;

--
-- Name: authenticator_key; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.authenticator_key (
    user_id bigint NOT NULL,
    encrypted_key text NOT NULL,
    header text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.authenticator_key OWNER TO pguser;

--
-- Name: casting; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.casting (
    id uuid NOT NULL,
    code character varying(16) NOT NULL,
    public_key character varying(512) NOT NULL,
    collection_id bigint,
    cast_user bigint,
    encrypted_payload text,
    token character varying(512),
    is_deleted boolean DEFAULT false,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    last_used_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    ip text NOT NULL
);


ALTER TABLE public.casting OWNER TO pguser;

--
-- Name: collection_files; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.collection_files (
    file_id bigint NOT NULL,
    collection_id bigint NOT NULL,
    encrypted_key text NOT NULL,
    key_decryption_nonce text NOT NULL,
    is_deleted boolean DEFAULT false,
    updation_time bigint NOT NULL,
    c_owner_id bigint,
    f_owner_id bigint,
    created_at bigint DEFAULT public.now_utc_micro_seconds()
);


ALTER TABLE public.collection_files OWNER TO pguser;

--
-- Name: collection_shares; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.collection_shares (
    collection_id bigint NOT NULL,
    from_user_id bigint NOT NULL,
    to_user_id bigint NOT NULL,
    encrypted_key text NOT NULL,
    updation_time bigint NOT NULL,
    is_deleted boolean DEFAULT false,
    role_type public.role_enum DEFAULT 'VIEWER'::public.role_enum,
    magic_metadata jsonb
);


ALTER TABLE public.collection_shares OWNER TO pguser;

--
-- Name: collections; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.collections (
    collection_id bigint NOT NULL,
    owner_id bigint NOT NULL,
    encrypted_key text NOT NULL,
    key_decryption_nonce text NOT NULL,
    name text,
    type text NOT NULL,
    attributes jsonb NOT NULL,
    updation_time bigint NOT NULL,
    is_deleted boolean DEFAULT false,
    encrypted_name text,
    name_decryption_nonce text,
    magic_metadata jsonb,
    pub_magic_metadata jsonb,
    app public.app DEFAULT 'photos'::public.app NOT NULL
);


ALTER TABLE public.collections OWNER TO pguser;

--
-- Name: collections_collection_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

ALTER TABLE public.collections ALTER COLUMN collection_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.collections_collection_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: data_cleanup; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.data_cleanup (
    user_id bigint NOT NULL,
    stage public.stage_enum DEFAULT 'scheduled'::public.stage_enum NOT NULL,
    stage_schedule_time bigint DEFAULT (public.now_utc_micro_seconds() + (((((7 * (24)::bigint) * 60) * 60) * 1000) * 1000)) NOT NULL,
    stage_attempt_count integer DEFAULT 0 NOT NULL,
    status text DEFAULT ''::text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.data_cleanup OWNER TO pguser;

--
-- Name: embeddings; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.embeddings (
    file_id bigint NOT NULL,
    owner_id bigint NOT NULL,
    model public.model NOT NULL,
    encrypted_embedding text,
    decryption_header text,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    size integer,
    version integer DEFAULT 1,
    datacenters public.s3region[] DEFAULT '{b2-eu-cen}'::public.s3region[]
);


ALTER TABLE public.embeddings OWNER TO pguser;

--
-- Name: emergency_contact; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.emergency_contact (
    user_id bigint NOT NULL,
    emergency_contact_id bigint NOT NULL,
    state text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    notice_period_in_hrs integer NOT NULL,
    encrypted_key text,
    CONSTRAINT chk_encrypted_key_null CHECK ((((state = ANY (ARRAY['REVOKED'::text, 'DELETED'::text, 'CONTACT_LEFT'::text, 'CONTACT_DENIED'::text])) AND (encrypted_key IS NULL)) OR ((state <> ALL (ARRAY['REVOKED'::text, 'DELETED'::text, 'CONTACT_LEFT'::text, 'CONTACT_DENIED'::text])) AND (encrypted_key IS NOT NULL)))),
    CONSTRAINT chk_user_id_not_equal_emergency_contact_id CHECK ((user_id <> emergency_contact_id)),
    CONSTRAINT emergency_contact_state_check CHECK ((state = ANY (ARRAY['INVITED'::text, 'ACCEPTED'::text, 'REVOKED'::text, 'DELETED'::text, 'CONTACT_LEFT'::text, 'CONTACT_DENIED'::text])))
);


ALTER TABLE public.emergency_contact OWNER TO pguser;

--
-- Name: emergency_recovery; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.emergency_recovery (
    id uuid NOT NULL,
    user_id bigint NOT NULL,
    emergency_contact_id bigint NOT NULL,
    status text NOT NULL,
    wait_till bigint,
    next_reminder_at bigint,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    CONSTRAINT emergency_recovery_status_check CHECK ((status = ANY (ARRAY['WAITING'::text, 'REJECTED'::text, 'RECOVERED'::text, 'STOPPED'::text, 'READY'::text])))
);


ALTER TABLE public.emergency_recovery OWNER TO pguser;

--
-- Name: entity_data; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.entity_data (
    user_id bigint NOT NULL,
    type text NOT NULL,
    encrypted_data text,
    header text,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    is_deleted boolean DEFAULT false,
    id text NOT NULL,
    CONSTRAINT entity_data_state_constraint CHECK ((((is_deleted IS TRUE) AND (encrypted_data IS NULL)) OR ((is_deleted IS FALSE) AND (encrypted_data IS NOT NULL))))
);


ALTER TABLE public.entity_data OWNER TO pguser;

--
-- Name: entity_key; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.entity_key (
    user_id bigint NOT NULL,
    type text NOT NULL,
    encrypted_key text NOT NULL,
    header text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.entity_key OWNER TO pguser;

--
-- Name: families; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.families (
    id uuid NOT NULL,
    admin_id bigint NOT NULL,
    member_id bigint NOT NULL,
    status text NOT NULL,
    token text,
    percentage integer DEFAULT '-1'::integer NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    CONSTRAINT families_member_state_constraint CHECK ((((admin_id <> member_id) AND (status <> ALL (ARRAY['SELF'::text, 'CLOSED'::text]))) OR ((admin_id = member_id) AND (status = ANY (ARRAY['SELF'::text, 'CLOSED'::text]))))),
    CONSTRAINT families_status_check CHECK ((status = ANY (ARRAY['SELF'::text, 'CLOSED'::text, 'INVITED'::text, 'ACCEPTED'::text, 'DECLINED'::text, 'REVOKED'::text, 'REMOVED'::text, 'LEFT'::text])))
);


ALTER TABLE public.families OWNER TO pguser;

--
-- Name: file_data; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.file_data (
    file_id bigint NOT NULL,
    user_id bigint NOT NULL,
    data_type public.object_type NOT NULL,
    size bigint NOT NULL,
    latest_bucket public.s3region NOT NULL,
    replicated_buckets public.s3region[] DEFAULT '{}'::public.s3region[] NOT NULL,
    delete_from_buckets public.s3region[] DEFAULT '{}'::public.s3region[] NOT NULL,
    inflight_rep_buckets public.s3region[] DEFAULT '{}'::public.s3region[] NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    pending_sync boolean DEFAULT true NOT NULL,
    sync_locked_till bigint DEFAULT 0 NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    obj_id text,
    obj_nonce text,
    obj_size integer
);


ALTER TABLE public.file_data OWNER TO pguser;

--
-- Name: files; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.files (
    file_id bigint NOT NULL,
    owner_id bigint NOT NULL,
    file_decryption_header text NOT NULL,
    thumbnail_decryption_header text NOT NULL,
    metadata_decryption_header text NOT NULL,
    encrypted_metadata text NOT NULL,
    updation_time bigint NOT NULL,
    magic_metadata jsonb,
    pub_magic_metadata jsonb,
    info jsonb
);


ALTER TABLE public.files OWNER TO pguser;

--
-- Name: files_file_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

CREATE SEQUENCE public.files_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.files_file_id_seq OWNER TO pguser;

--
-- Name: files_file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pguser
--

ALTER SEQUENCE public.files_file_id_seq OWNED BY public.files.file_id;


--
-- Name: kex_store; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.kex_store (
    id text NOT NULL,
    wrapped_key text NOT NULL,
    added_at bigint NOT NULL
);


ALTER TABLE public.kex_store OWNER TO pguser;

--
-- Name: key_attributes; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.key_attributes (
    user_id bigint NOT NULL,
    kek_salt text NOT NULL,
    kek_hash_bytes bytea,
    encrypted_key text NOT NULL,
    key_decryption_nonce text NOT NULL,
    public_key text NOT NULL,
    encrypted_secret_key text NOT NULL,
    secret_key_decryption_nonce text NOT NULL,
    mem_limit bigint DEFAULT 67108864,
    ops_limit integer DEFAULT 2,
    master_key_encrypted_with_recovery_key text,
    master_key_decryption_nonce text,
    recovery_key_encrypted_with_master_key text,
    recovery_key_decryption_nonce text,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.key_attributes OWNER TO pguser;

--
-- Name: notification_history; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.notification_history (
    user_id bigint NOT NULL,
    template_id text NOT NULL,
    sent_time bigint NOT NULL
);


ALTER TABLE public.notification_history OWNER TO pguser;

--
-- Name: object_copies; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.object_copies (
    object_key text NOT NULL,
    b2 bigint,
    want_b2 boolean,
    wasabi bigint,
    want_wasabi boolean,
    scw bigint,
    want_scw boolean,
    last_attempt bigint DEFAULT 0 NOT NULL
);


ALTER TABLE public.object_copies OWNER TO pguser;

--
-- Name: object_keys; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.object_keys (
    file_id bigint NOT NULL,
    o_type public.object_type NOT NULL,
    object_key text NOT NULL,
    size bigint NOT NULL,
    datacenters public.s3region[] NOT NULL,
    is_deleted boolean DEFAULT false,
    created_at bigint DEFAULT public.now_utc_micro_seconds(),
    updated_at bigint DEFAULT public.now_utc_micro_seconds()
);


ALTER TABLE public.object_keys OWNER TO pguser;

--
-- Name: otts; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.otts (
    ott text NOT NULL,
    creation_time bigint NOT NULL,
    expiration_time bigint NOT NULL,
    email text,
    email_hash text,
    wrong_attempt integer DEFAULT 0 NOT NULL,
    app public.app DEFAULT 'photos'::public.app NOT NULL
);


ALTER TABLE public.otts OWNER TO pguser;

--
-- Name: passkey_credentials; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.passkey_credentials (
    passkey_id uuid NOT NULL,
    credential_id text NOT NULL,
    public_key text NOT NULL,
    attestation_type text NOT NULL,
    authenticator_transports text NOT NULL,
    credential_flags text NOT NULL,
    authenticator text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.passkey_credentials OWNER TO pguser;

--
-- Name: passkey_login_sessions; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.passkey_login_sessions (
    user_id bigint NOT NULL,
    session_id text NOT NULL,
    creation_time bigint NOT NULL,
    expiration_time bigint NOT NULL,
    token_fetch_cnt integer DEFAULT 0,
    verified_at bigint,
    token_data jsonb
);


ALTER TABLE public.passkey_login_sessions OWNER TO pguser;

--
-- Name: passkeys; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.passkeys (
    id uuid NOT NULL,
    user_id bigint NOT NULL,
    friendly_name text NOT NULL,
    deleted_at bigint,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.passkeys OWNER TO pguser;

--
-- Name: public_abuse_report; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.public_abuse_report (
    share_id bigint,
    ip text NOT NULL,
    user_agent text NOT NULL,
    url text NOT NULL,
    reason text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    details jsonb
);


ALTER TABLE public.public_abuse_report OWNER TO pguser;

--
-- Name: public_collection_access_history; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.public_collection_access_history (
    share_id bigint,
    ip text NOT NULL,
    user_agent text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.public_collection_access_history OWNER TO pguser;

--
-- Name: public_collection_tokens; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.public_collection_tokens (
    id bigint NOT NULL,
    collection_id bigint NOT NULL,
    access_token text NOT NULL,
    is_disabled boolean DEFAULT false NOT NULL,
    valid_till bigint DEFAULT 0 NOT NULL,
    device_limit integer DEFAULT 0 NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    pw_hash text,
    pw_nonce text,
    mem_limit bigint,
    ops_limit bigint,
    enable_download boolean DEFAULT true NOT NULL,
    enable_comment boolean DEFAULT false NOT NULL,
    enable_collect boolean DEFAULT false NOT NULL,
    enable_join boolean DEFAULT true NOT NULL,
    CONSTRAINT pct_pw_state_constraint CHECK ((((pw_hash IS NULL) AND (pw_nonce IS NULL)) OR ((pw_hash IS NOT NULL) AND (pw_nonce IS NOT NULL))))
);


ALTER TABLE public.public_collection_tokens OWNER TO pguser;

--
-- Name: public_collection_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

ALTER TABLE public.public_collection_tokens ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.public_collection_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: push_tokens; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.push_tokens (
    user_id bigint NOT NULL,
    fcm_token text NOT NULL,
    apns_token text,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    last_notified_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.push_tokens OWNER TO pguser;

--
-- Name: queue; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.queue (
    queue_id integer NOT NULL,
    queue_name text NOT NULL,
    item text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds(),
    updated_at bigint DEFAULT public.now_utc_micro_seconds(),
    is_deleted boolean DEFAULT false
);


ALTER TABLE public.queue OWNER TO pguser;

--
-- Name: queue_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

CREATE SEQUENCE public.queue_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.queue_queue_id_seq OWNER TO pguser;

--
-- Name: queue_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pguser
--

ALTER SEQUENCE public.queue_queue_id_seq OWNED BY public.queue.queue_id;


--
-- Name: referral_codes; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.referral_codes (
    code character varying(255) NOT NULL,
    user_id bigint NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.referral_codes OWNER TO pguser;

--
-- Name: referral_tracking; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.referral_tracking (
    invitor_id bigint NOT NULL,
    invitee_id bigint NOT NULL,
    plan_type text NOT NULL,
    invitee_on_paid_plan boolean DEFAULT false,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    CONSTRAINT referral_tracking_plan_type_check CHECK ((plan_type = '10_GB_ON_UPGRADE'::text))
);


ALTER TABLE public.referral_tracking OWNER TO pguser;

--
-- Name: remote_store; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.remote_store (
    user_id bigint NOT NULL,
    key_name text NOT NULL,
    key_value text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.remote_store OWNER TO pguser;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.schema_migrations (
    version bigint NOT NULL,
    dirty boolean NOT NULL
);


ALTER TABLE public.schema_migrations OWNER TO pguser;

--
-- Name: srp_auth; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.srp_auth (
    user_id bigint NOT NULL,
    srp_user_id uuid NOT NULL,
    salt text NOT NULL,
    verifier text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.srp_auth OWNER TO pguser;

--
-- Name: srp_sessions; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.srp_sessions (
    id uuid NOT NULL,
    srp_user_id uuid NOT NULL,
    server_key text NOT NULL,
    srp_a text NOT NULL,
    has_verified boolean DEFAULT false NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.srp_sessions OWNER TO pguser;

--
-- Name: storage_bonus; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.storage_bonus (
    bonus_id text NOT NULL,
    type text NOT NULL,
    user_id bigint NOT NULL,
    storage bigint NOT NULL,
    valid_till bigint DEFAULT 0 NOT NULL,
    revoke_reason text,
    is_revoked boolean DEFAULT false NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    CONSTRAINT storage_bonus_type_check CHECK ((type = ANY (ARRAY['REFERRAL'::text, 'SIGN_UP'::text, 'ANNIVERSARY'::text, 'ADD_ON_BF_2023'::text, 'ADD_ON_SUPPORT'::text, 'ADD_ON_BF_2024'::text])))
);


ALTER TABLE public.storage_bonus OWNER TO pguser;

--
-- Name: subscription_logs; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.subscription_logs (
    log_id integer NOT NULL,
    user_id bigint NOT NULL,
    payment_provider text NOT NULL,
    notification jsonb NOT NULL,
    verification_response jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.subscription_logs OWNER TO pguser;

--
-- Name: subscription_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

CREATE SEQUENCE public.subscription_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscription_logs_log_id_seq OWNER TO pguser;

--
-- Name: subscription_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pguser
--

ALTER SEQUENCE public.subscription_logs_log_id_seq OWNED BY public.subscription_logs.log_id;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.subscriptions (
    subscription_id integer NOT NULL,
    user_id bigint NOT NULL,
    storage bigint NOT NULL,
    original_transaction_id text NOT NULL,
    expiry_time bigint NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    product_id text NOT NULL,
    payment_provider text NOT NULL,
    latest_verification_data text,
    attributes jsonb NOT NULL
);


ALTER TABLE public.subscriptions OWNER TO pguser;

--
-- Name: subscriptions_subscription_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

CREATE SEQUENCE public.subscriptions_subscription_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscriptions_subscription_id_seq OWNER TO pguser;

--
-- Name: subscriptions_subscription_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pguser
--

ALTER SEQUENCE public.subscriptions_subscription_id_seq OWNED BY public.subscriptions.subscription_id;


--
-- Name: task_lock; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.task_lock (
    task_name text NOT NULL,
    lock_until bigint NOT NULL,
    locked_at bigint NOT NULL,
    locked_by text NOT NULL
);


ALTER TABLE public.task_lock OWNER TO pguser;

--
-- Name: temp_objects; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.temp_objects (
    object_key text NOT NULL,
    expiration_time bigint NOT NULL,
    is_multipart boolean DEFAULT false NOT NULL,
    upload_id text,
    bucket_id public.s3region
);


ALTER TABLE public.temp_objects OWNER TO pguser;

--
-- Name: temp_srp_setup; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.temp_srp_setup (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    srp_user_id uuid NOT NULL,
    user_id bigint NOT NULL,
    salt text NOT NULL,
    verifier text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.temp_srp_setup OWNER TO pguser;

--
-- Name: temp_two_factor; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.temp_two_factor (
    user_id bigint NOT NULL,
    two_factor_secret_hash text,
    encrypted_two_factor_secret bytea,
    two_factor_secret_decryption_nonce bytea,
    creation_time bigint NOT NULL,
    expiration_time bigint NOT NULL
);


ALTER TABLE public.temp_two_factor OWNER TO pguser;

--
-- Name: tokens; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.tokens (
    user_id bigint NOT NULL,
    token text NOT NULL,
    creation_time bigint NOT NULL,
    ip text,
    user_agent text,
    is_deleted boolean DEFAULT false NOT NULL,
    last_used_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    app public.app DEFAULT 'photos'::public.app NOT NULL
);


ALTER TABLE public.tokens OWNER TO pguser;

--
-- Name: trash; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.trash (
    file_id bigint NOT NULL,
    user_id bigint NOT NULL,
    collection_id bigint NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    is_restored boolean DEFAULT false NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    delete_by bigint NOT NULL,
    CONSTRAINT trash_state_constraint CHECK (((is_deleted IS FALSE) OR (is_restored IS FALSE)))
);


ALTER TABLE public.trash OWNER TO pguser;

--
-- Name: two_factor; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.two_factor (
    user_id bigint NOT NULL,
    two_factor_secret_hash text,
    encrypted_two_factor_secret bytea,
    two_factor_secret_decryption_nonce bytea,
    recovery_encrypted_two_factor_secret text,
    recovery_two_factor_secret_decryption_nonce text
);


ALTER TABLE public.two_factor OWNER TO pguser;

--
-- Name: two_factor_recovery; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.two_factor_recovery (
    user_id bigint NOT NULL,
    enable_admin_mfa_reset boolean DEFAULT true NOT NULL,
    server_passkey_secret_data bytea,
    server_passkey_secret_nonce bytea,
    user_passkey_secret_data text,
    user_passkey_secret_nonce text,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL,
    updated_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.two_factor_recovery OWNER TO pguser;

--
-- Name: two_factor_sessions; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.two_factor_sessions (
    user_id bigint NOT NULL,
    session_id text NOT NULL,
    creation_time bigint NOT NULL,
    expiration_time bigint NOT NULL,
    wrong_attempt integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.two_factor_sessions OWNER TO pguser;

--
-- Name: usage; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.usage (
    user_id bigint NOT NULL,
    storage_consumed bigint NOT NULL
);


ALTER TABLE public.usage OWNER TO pguser;

--
-- Name: users; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    name text,
    creation_time bigint NOT NULL,
    encrypted_email bytea,
    email_decryption_nonce bytea,
    email_hash text,
    is_two_factor_enabled boolean DEFAULT false NOT NULL,
    family_admin_id bigint,
    email_mfa boolean DEFAULT false NOT NULL,
    source text,
    delete_feedback jsonb
);


ALTER TABLE public.users OWNER TO pguser;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: pguser
--

ALTER TABLE public.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: webauthn_sessions; Type: TABLE; Schema: public; Owner: pguser
--

CREATE TABLE public.webauthn_sessions (
    id uuid NOT NULL,
    challenge text NOT NULL,
    user_id bigint NOT NULL,
    allowed_credential_ids text NOT NULL,
    expires_at bigint NOT NULL,
    user_verification_requirement text NOT NULL,
    extensions text NOT NULL,
    created_at bigint DEFAULT public.now_utc_micro_seconds() NOT NULL
);


ALTER TABLE public.webauthn_sessions OWNER TO pguser;

--
-- Name: files file_id; Type: DEFAULT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.files ALTER COLUMN file_id SET DEFAULT nextval('public.files_file_id_seq'::regclass);


--
-- Name: queue queue_id; Type: DEFAULT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.queue ALTER COLUMN queue_id SET DEFAULT nextval('public.queue_queue_id_seq'::regclass);


--
-- Name: subscription_logs log_id; Type: DEFAULT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscription_logs ALTER COLUMN log_id SET DEFAULT nextval('public.subscription_logs_log_id_seq'::regclass);


--
-- Name: subscriptions subscription_id; Type: DEFAULT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN subscription_id SET DEFAULT nextval('public.subscriptions_subscription_id_seq'::regclass);


--
-- Data for Name: authenticator_entity; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.authenticator_entity (id, user_id, encrypted_data, header, created_at, updated_at, is_deleted) FROM stdin;
\.


--
-- Data for Name: authenticator_key; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.authenticator_key (user_id, encrypted_key, header, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: casting; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.casting (id, code, public_key, collection_id, cast_user, encrypted_payload, token, is_deleted, created_at, last_used_at, ip) FROM stdin;
\.


--
-- Data for Name: collection_files; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.collection_files (file_id, collection_id, encrypted_key, key_decryption_nonce, is_deleted, updation_time, c_owner_id, f_owner_id, created_at) FROM stdin;
10000000	1580559962386438	+Cmc5jGF8IvvHpfGtxs4sxpPp8HNo/IhJRXIGyVoRdqucIX4AYVumbojT+iXU/m5	H9/i0TnlK3Am2qJ+RVEiPjMn2OgcxEZ3	f	1739698159035508	1580559962386438	1580559962386438	1739698159042643
\.


--
-- Data for Name: collection_shares; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.collection_shares (collection_id, from_user_id, to_user_id, encrypted_key, updation_time, is_deleted, role_type, magic_metadata) FROM stdin;
\.


--
-- Data for Name: collections; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.collections (collection_id, owner_id, encrypted_key, key_decryption_nonce, name, type, attributes, updation_time, is_deleted, encrypted_name, name_decryption_nonce, magic_metadata, pub_magic_metadata, app) FROM stdin;
1580559962386438	1580559962386438	2ZB4ZII7zzBwmCK4k6C+E85VeBvsMkG0rbzLrITABOHejCFXXmMW0uyRfFJxqoSj	XfzAX9WPyBMALiDunroy9He0LPo4CyRt		uncategorized	{"version": 0}	1739698159035508	f	DSJC+NphpyN+6jK26pSNqSJhy9rgFaEeSV/E7+4=	y7PibIISieS2L4Mw+tMYswZ/0ZR0NFHm	\N	\N	photos
\.


--
-- Data for Name: data_cleanup; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.data_cleanup (user_id, stage, stage_schedule_time, stage_attempt_count, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: embeddings; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.embeddings (file_id, owner_id, model, encrypted_embedding, decryption_header, updated_at, size, version, datacenters) FROM stdin;
\.


--
-- Data for Name: emergency_contact; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.emergency_contact (user_id, emergency_contact_id, state, created_at, updated_at, notice_period_in_hrs, encrypted_key) FROM stdin;
\.


--
-- Data for Name: emergency_recovery; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.emergency_recovery (id, user_id, emergency_contact_id, status, wait_till, next_reminder_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: entity_data; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.entity_data (user_id, type, encrypted_data, header, created_at, updated_at, is_deleted, id) FROM stdin;
\.


--
-- Data for Name: entity_key; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.entity_key (user_id, type, encrypted_key, header, created_at, updated_at) FROM stdin;
1580559962386438	location	hh3d7oQmVNJM+nXyCUxSjQXdCF4az3IJdwBZarURdtor/kIPpDdGYQeQUHjRiXHJ	BeHBlBriOiP7THIbgyCJoEHbbmFykL7g	1738010878068849	1738010878068849
\.


--
-- Data for Name: families; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.families (id, admin_id, member_id, status, token, percentage, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: file_data; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.file_data (file_id, user_id, data_type, size, latest_bucket, replicated_buckets, delete_from_buckets, inflight_rep_buckets, is_deleted, pending_sync, sync_locked_till, created_at, updated_at, obj_id, obj_nonce, obj_size) FROM stdin;
\.


--
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.files (file_id, owner_id, file_decryption_header, thumbnail_decryption_header, metadata_decryption_header, encrypted_metadata, updation_time, magic_metadata, pub_magic_metadata, info) FROM stdin;
10000000	1580559962386438	HvUPP6WAoEIFsIx2fkiddhExe9W3K2eU	+uT6xZepfbEIv9l2IqN8+r3AvUcqiyl3	oMP/GGh3AtmdUtc17EpXBDEHCTzS/E/D	Pxj0Sw8eOnLstzQHuzVkoGdopu2DwXincwLP8M2pt0EvhwwcvghMJc0/iTdfcAyOCwyoqnTF8YyH43XJariOg54gfBZKjjL8eD3dVq4aN5zUAfJxHLv7X//AulVwwzxnK8ShP5463UKwJr60iFqEdm/+Bo1lFuKXEqGnJhfYDNItNlIi595nrFlUYKimqGW/qJCWya7tXCvsbZnJoPoa+JVPiWW5U5uPeNrkl6nlU62HcUJd/KEVuGZckRZBi1tw8j7BS7EM75xN5oDxJF3r7RIBGH4g1twT42dYS1MRFYM=	1739698159035508	\N	{"data": "0uzArElPEW7Vk/BRbpdI+UgEuDlv54mrVEeeUdTvsA8WWDbylo/3r2FPQOptVJy2jAgAo4bhiSJah3CMFniF62Fv3YT7WA==", "count": 3, "header": "Um5TIgQbTYIx5Ju3X1dLvqMhXn7hv2TE", "version": 1}	{"fileSize": 3582, "thumbSize": 33595}
\.


--
-- Data for Name: kex_store; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.kex_store (id, wrapped_key, added_at) FROM stdin;
\.


--
-- Data for Name: key_attributes; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.key_attributes (user_id, kek_salt, kek_hash_bytes, encrypted_key, key_decryption_nonce, public_key, encrypted_secret_key, secret_key_decryption_nonce, mem_limit, ops_limit, master_key_encrypted_with_recovery_key, master_key_decryption_nonce, recovery_key_encrypted_with_master_key, recovery_key_decryption_nonce, created_at) FROM stdin;
1580559962386438	5ybgr3AiubqN5ptNyeK5Iw==	\\x	AxUdj4QJ00M0qxQCuRNA09qbGxzut6yjIvuoQKEc3cbb6f1sJlenJHHM+wFMH+Tg	cRu9Tij18NPvU8OpVNz1J57PbfcYVzHH	ng2rPNuvTkbeM/wpARwPxq4S6OEZgRHs54B05dXpiyk=	aQEPrlaxe0JHv4Sd7VcDLV8wbdnqlvDCQzM0YgAPOBZhERdD9cmPPZ2KUVgjFE05	/UUOcroZDLo2jBkqyaxvEXG72icNhLhG	1073741824	4	rkgkqMD+A2aOqcyx3IFNaPdKaJWqEX+iVrZpkw8/GUSNiMQlna616ldPooRvHCc8	v6MjV1PtuXUOicDRKmL2B+sSwf5ohePC	1V5AV79JxGTM/LuY9Hz6fV2wLjRsDrfLIb6F1D3m7wTvVcMdvc9Q5fICPHyg+a78	i04D7U6nuHIo+oNfdDhEzUMqUtMqh7BS	1738010876222704
\.


--
-- Data for Name: notification_history; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.notification_history (user_id, template_id, sent_time) FROM stdin;
\.


--
-- Data for Name: object_copies; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.object_copies (object_key, b2, want_b2, wasabi, want_wasabi, scw, want_scw, last_attempt) FROM stdin;
1580559962386438/ce17ea8f-60cb-4549-a308-edbe2097f2db	1739698159042643	t	\N	t	\N	t	0
1580559962386438/adca0074-0e1f-4e27-877c-1b460c9bbc0f	1739698159042643	t	\N	t	\N	f	0
\.


--
-- Data for Name: object_keys; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.object_keys (file_id, o_type, object_key, size, datacenters, is_deleted, created_at, updated_at) FROM stdin;
10000000	file	1580559962386438/ce17ea8f-60cb-4549-a308-edbe2097f2db	3582	{b2-eu-cen}	f	1739698159042643	1739698159042643
10000000	thumbnail	1580559962386438/adca0074-0e1f-4e27-877c-1b460c9bbc0f	33595	{b2-eu-cen}	f	1739698159042643	1739698159042643
\.


--
-- Data for Name: otts; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.otts (ott, creation_time, expiration_time, email, email_hash, wrong_attempt, app) FROM stdin;
\.


--
-- Data for Name: passkey_credentials; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.passkey_credentials (passkey_id, credential_id, public_key, attestation_type, authenticator_transports, credential_flags, authenticator, created_at) FROM stdin;
\.


--
-- Data for Name: passkey_login_sessions; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.passkey_login_sessions (user_id, session_id, creation_time, expiration_time, token_fetch_cnt, verified_at, token_data) FROM stdin;
\.


--
-- Data for Name: passkeys; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.passkeys (id, user_id, friendly_name, deleted_at, created_at) FROM stdin;
\.


--
-- Data for Name: public_abuse_report; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.public_abuse_report (share_id, ip, user_agent, url, reason, created_at, details) FROM stdin;
\.


--
-- Data for Name: public_collection_access_history; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.public_collection_access_history (share_id, ip, user_agent, created_at) FROM stdin;
\.


--
-- Data for Name: public_collection_tokens; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.public_collection_tokens (id, collection_id, access_token, is_disabled, valid_till, device_limit, created_at, updated_at, pw_hash, pw_nonce, mem_limit, ops_limit, enable_download, enable_comment, enable_collect, enable_join) FROM stdin;
\.


--
-- Data for Name: push_tokens; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.push_tokens (user_id, fcm_token, apns_token, created_at, updated_at, last_notified_at) FROM stdin;
\.


--
-- Data for Name: queue; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.queue (queue_id, queue_name, item, created_at, updated_at, is_deleted) FROM stdin;
\.


--
-- Data for Name: referral_codes; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.referral_codes (code, user_id, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: referral_tracking; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.referral_tracking (invitor_id, invitee_id, plan_type, invitee_on_paid_plan, created_at) FROM stdin;
\.


--
-- Data for Name: remote_store; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.remote_store (user_id, key_name, key_value, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.schema_migrations (version, dirty) FROM stdin;
95	f
\.


--
-- Data for Name: srp_auth; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.srp_auth (user_id, srp_user_id, salt, verifier, created_at, updated_at) FROM stdin;
1580559962386438	5e0d052d-64af-4313-9381-917dbcbc59e9	0WFaJZeMDeEDKQXjQ1lNYg==	g6Mcwhct9eg/QuTFBn8p+a2iDfX2aD3hiIhqfGJn0XOSPykiGQagCWKDFQAxzP6dVhiYYLcmxXxcP7a/ycbQGLq/fKCTjU65VRDdBAmA9p9N/0p+mEzUg1xxVsjZDKIvdqqWmQWf+pqGdgjScMfM0bkhnREhOgIYtwyJZv3oX97NWUOhhfvhnyB/edAX7I83iJYvCCY8B3yW45jPWBySoMu1QbxKNodTCnUhDA+zaVaRt5eW8rT/7aDPGbs/8v5tKdFUUTreCdkx6wcBNTu3nyKp8/0s6THCSsywWA/+yXeFiVWv4gbeZYDJsNSQnyhs7ZVRLl+BgmWgDeOX1WNEZMK8uU5q6RhzOpwcSakxrRaFSDYJO4KbwlqLMYzGxYDXqklLGaGiC/6Ef0iaQBv85iSGXTltXyiREcJB1APlm/XEhQrAmOSJjyihHxzyWDYUZ0P4hY2gHU62X2RYpIafmo5abP96jHFD9M1G32Szz7YsT1QjOcrX3Lh6lIvx+aVoUUlduwxTiQOH7vd8CYidL2k6PxM2U31chGiHeK8UR2lesa8gk5aiXHob9GPJoS15X/lLj5gDkIitFPNsrsKiE1MEfw4Xja419zqfhkfWZCh31dSLnPmfRq1i0mnFMblDyhFZB4BAifvhM35O7/oYmhWJKpSy2We3o7Jwv9FthCs=	1738010876421000	1738010876421000
\.


--
-- Data for Name: srp_sessions; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.srp_sessions (id, srp_user_id, server_key, srp_a, has_verified, attempt_count, created_at, updated_at) FROM stdin;
9d2e3b32-d6e5-467a-a068-89bdc4c16257	5e0d052d-64af-4313-9381-917dbcbc59e9	clmDhyM3x9SLAysknSDiNCBPnptv0dr/QCnX/f2G67A=	6pQTzCDkmbRP3E94Kx+hq17su+9g+HZpzP47I262ULqclguZ3vBSE3MDK/w+9vPKLzbyJNdz/Z4tBK8tAzARBM+3ypJ21b8oxxItn+z/fOGUvB/UL1m2lPnpudIeZrHf+2ims5iPy1QaykEE8ufwt74zH7K8RQXJ6QGePp/UodVCyRzlgj1j2l8WD2uVCfMUhipt6UW1cur7E4tJ9caToekd2uYzJcqUcC6l1HTZUx4LhM825lFdLANQiVJo3w+te5NdWA5RyEpCy7Ra2f1w775snhVv1UOZZhMVxeUm1tPqwAv7AjD3MWRJ1F+8feeVsimzb/uTPqCNBwav4/rAyLjvkk0YiWw4Co+bk/ksNngfYCsAO57VQ33YVkcu5ASRcyeHpMpgmUx/TS+LmdEKvmtIvLToVCnK1dQomfS/g8qefplBd09oLEZogH60/rqfch3wBIPsSuAt/4mr8W3fOs9NgZoC+qz8W7kIOeH9lHW8mIbbTYHTsAqN7200EZVf0YE98eSkdZZLTdWcAe2DKmgDy2O+C62uzjJN9x52W4HUecx4Y3zWltGOZSnkffGO5vUdmA9PVvrAE/gozxGQoq6IRW/GFh3SsmFKhpnzMpV3VIpm/hR0oolVzazPUfyARKDRrTEwZvz1cWBSMPsFLdfNdmJ40HXrW5J5StLWXrE=	t	0	1738010876306410	1738010876415190
933a0194-d241-4320-96da-77f38f5282ef	5e0d052d-64af-4313-9381-917dbcbc59e9	poZVLgZI+XS8AJ9PEkBxw7seK4Td+g05mpqTU6Jwnak=	4gKSQeZK3iKwQvlsH7xjfTKYnoRRqTM3ol5alA82CnqyxSS/Lm7QN3SzinO5PvV02e778kKTBsEyMimhEOOkWzVVUQqu904aDMFokqOk1VEys5wk9ARR3v7alo9DEB2C39Cjdof4QJXmF5V+3F6Wuxzr2JxO0X1rFatXX634bmih1ZOLlCEU8/76qWyQ3lqFatyhsJvBBLQvPw9qOWEXwgJqU+r/nWJD1TseTRKEkJbMElHqHkxdPRIP4b8m35/57fDFg7VEGXP1i49NqUJ6smzLAhfUe2ZF1tHRl3GcUdCj7q0gqWd+NXTEOwsP+Tz3ku6OIwr55mcuTI6B40uYwJSjWfRx+GEKRvCd403SQVXXPtAXef1ScIUVdMyREFY/zutI/yN1+TptKjzIJZR9CyEkKQ8/yMPtuzuv/L1ph/BC3VqZNRUqoumhtWBpWtP0zZnMG1ZC1y4NG1QKw4Pr3RA1ccvdaY27FrkwWAZlUf18IW7G1EVIc5QWr6WCyTT27Lpu+gfAfbw9FSzg6LzF6v6tbO8niVZifWtynpF6tAziocn/5uEexYjg46Kn1lzkC++/d4ItJRZ4VbEM8swUjXaSZNI3lBR0r7iak4dBTaOg8FcqLbHQ1UauwmFs42Z3YgTNzZYP1g7q0nyhpJohRTNpiSbG9LBydcTYuXFvw6c=	t	0	1739698150974828	1739698151085103
\.


--
-- Data for Name: storage_bonus; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.storage_bonus (bonus_id, type, user_id, storage, valid_till, revoke_reason, is_revoked, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: subscription_logs; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.subscription_logs (log_id, user_id, payment_provider, notification, verification_response, created_at) FROM stdin;
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.subscriptions (subscription_id, user_id, storage, original_transaction_id, expiry_time, created_at, product_id, payment_provider, latest_verification_data, attributes) FROM stdin;
1	1580559962386438	5368709120	none	4893684476202906	2025-01-27 20:47:56.205417	free		\N	{}
\.


--
-- Data for Name: task_lock; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.task_lock (task_name, lock_until, locked_at, locked_by) FROM stdin;
\.


--
-- Data for Name: temp_objects; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.temp_objects (object_key, expiration_time, is_multipart, upload_id, bucket_id) FROM stdin;
\.


--
-- Data for Name: temp_srp_setup; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.temp_srp_setup (id, session_id, srp_user_id, user_id, salt, verifier, created_at) FROM stdin;
98c386ce-eb30-4f6c-b565-426629c17a36	9d2e3b32-d6e5-467a-a068-89bdc4c16257	5e0d052d-64af-4313-9381-917dbcbc59e9	1580559962386438	0WFaJZeMDeEDKQXjQ1lNYg==	g6Mcwhct9eg/QuTFBn8p+a2iDfX2aD3hiIhqfGJn0XOSPykiGQagCWKDFQAxzP6dVhiYYLcmxXxcP7a/ycbQGLq/fKCTjU65VRDdBAmA9p9N/0p+mEzUg1xxVsjZDKIvdqqWmQWf+pqGdgjScMfM0bkhnREhOgIYtwyJZv3oX97NWUOhhfvhnyB/edAX7I83iJYvCCY8B3yW45jPWBySoMu1QbxKNodTCnUhDA+zaVaRt5eW8rT/7aDPGbs/8v5tKdFUUTreCdkx6wcBNTu3nyKp8/0s6THCSsywWA/+yXeFiVWv4gbeZYDJsNSQnyhs7ZVRLl+BgmWgDeOX1WNEZMK8uU5q6RhzOpwcSakxrRaFSDYJO4KbwlqLMYzGxYDXqklLGaGiC/6Ef0iaQBv85iSGXTltXyiREcJB1APlm/XEhQrAmOSJjyihHxzyWDYUZ0P4hY2gHU62X2RYpIafmo5abP96jHFD9M1G32Szz7YsT1QjOcrX3Lh6lIvx+aVoUUlduwxTiQOH7vd8CYidL2k6PxM2U31chGiHeK8UR2lesa8gk5aiXHob9GPJoS15X/lLj5gDkIitFPNsrsKiE1MEfw4Xja419zqfhkfWZCh31dSLnPmfRq1i0mnFMblDyhFZB4BAifvhM35O7/oYmhWJKpSy2We3o7Jwv9FthCs=	1738010876308649
\.


--
-- Data for Name: temp_two_factor; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.temp_two_factor (user_id, two_factor_secret_hash, encrypted_two_factor_secret, two_factor_secret_decryption_nonce, creation_time, expiration_time) FROM stdin;
\.


--
-- Data for Name: tokens; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.tokens (user_id, token, creation_time, ip, user_agent, is_deleted, last_used_at, app) FROM stdin;
1580559962386438	fJWwIOsSm73vCaS7AZdi47Mv2VZjUnCVGMSEFDrMukc=	1739698151090378	172.19.0.1	Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ente/1.7.9 Chrome/132.0.6834.194 Electron/34.1.1 Safari/537.36	f	1739698151237235	photos
\.


--
-- Data for Name: trash; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.trash (file_id, user_id, collection_id, is_deleted, is_restored, created_at, updated_at, delete_by) FROM stdin;
\.


--
-- Data for Name: two_factor; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.two_factor (user_id, two_factor_secret_hash, encrypted_two_factor_secret, two_factor_secret_decryption_nonce, recovery_encrypted_two_factor_secret, recovery_two_factor_secret_decryption_nonce) FROM stdin;
\.


--
-- Data for Name: two_factor_recovery; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.two_factor_recovery (user_id, enable_admin_mfa_reset, server_passkey_secret_data, server_passkey_secret_nonce, user_passkey_secret_data, user_passkey_secret_nonce, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: two_factor_sessions; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.two_factor_sessions (user_id, session_id, creation_time, expiration_time, wrong_attempt) FROM stdin;
\.


--
-- Data for Name: usage; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.usage (user_id, storage_consumed) FROM stdin;
1580559962386438	37177
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.users (user_id, name, creation_time, encrypted_email, email_decryption_nonce, email_hash, is_two_factor_enabled, family_admin_id, email_mfa, source, delete_feedback) FROM stdin;
1580559962386438	\N	1738010876195660	\\x0a3cac68920d64dee55a580906ea05cfc2f59dc90e6607d631ce554deea86fbc8f6418	\\x32e79ddc9dd1556dc50a7f7f5b415aa708b8e313818cdd37	xK/UOh893VRENEyTI+KthtDTZPyW5do/QqZ7y8xhUl8=	f	\N	f	\N	\N
\.


--
-- Data for Name: webauthn_sessions; Type: TABLE DATA; Schema: public; Owner: pguser
--

COPY public.webauthn_sessions (id, challenge, user_id, allowed_credential_ids, expires_at, user_verification_requirement, extensions, created_at) FROM stdin;
\.


--
-- Name: collections_collection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.collections_collection_id_seq', 1580559962386438, true);


--
-- Name: files_file_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.files_file_id_seq', 10000000, true);


--
-- Name: public_collection_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.public_collection_tokens_id_seq', 1, false);


--
-- Name: queue_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.queue_queue_id_seq', 1, false);


--
-- Name: subscription_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.subscription_logs_log_id_seq', 1, false);


--
-- Name: subscriptions_subscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.subscriptions_subscription_id_seq', 1, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: pguser
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1580559962386438, true);


--
-- Name: authenticator_entity authenticator_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.authenticator_entity
    ADD CONSTRAINT authenticator_entity_pkey PRIMARY KEY (id);


--
-- Name: authenticator_key authenticator_key_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.authenticator_key
    ADD CONSTRAINT authenticator_key_pkey PRIMARY KEY (user_id);


--
-- Name: casting casting_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.casting
    ADD CONSTRAINT casting_pkey PRIMARY KEY (id);


--
-- Name: collection_shares collection_shares_collection_id_from_user_id_to_user_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_shares
    ADD CONSTRAINT collection_shares_collection_id_from_user_id_to_user_id_key UNIQUE (collection_id, from_user_id, to_user_id);


--
-- Name: collections collections_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT collections_pkey PRIMARY KEY (collection_id);


--
-- Name: data_cleanup data_cleanup_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.data_cleanup
    ADD CONSTRAINT data_cleanup_pkey PRIMARY KEY (user_id);


--
-- Name: emergency_recovery emergency_recovery_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_recovery
    ADD CONSTRAINT emergency_recovery_pkey PRIMARY KEY (id);


--
-- Name: entity_data entity_data_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.entity_data
    ADD CONSTRAINT entity_data_pkey PRIMARY KEY (id);


--
-- Name: entity_key entity_key_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.entity_key
    ADD CONSTRAINT entity_key_pkey PRIMARY KEY (user_id, type);


--
-- Name: families families_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_pkey PRIMARY KEY (id);


--
-- Name: families families_token_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT families_token_key UNIQUE (token);


--
-- Name: file_data file_data_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.file_data
    ADD CONSTRAINT file_data_pkey PRIMARY KEY (file_id, data_type);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (file_id);


--
-- Name: kex_store kex_store_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.kex_store
    ADD CONSTRAINT kex_store_pkey PRIMARY KEY (id);


--
-- Name: key_attributes key_attributes_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.key_attributes
    ADD CONSTRAINT key_attributes_pkey PRIMARY KEY (user_id);


--
-- Name: object_copies object_copies_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.object_copies
    ADD CONSTRAINT object_copies_pkey PRIMARY KEY (object_key);


--
-- Name: object_keys object_keys_object_key_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.object_keys
    ADD CONSTRAINT object_keys_object_key_key UNIQUE (object_key);


--
-- Name: object_keys object_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.object_keys
    ADD CONSTRAINT object_keys_pkey PRIMARY KEY (file_id, o_type);


--
-- Name: passkey_credentials passkey_credentials_credential_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkey_credentials
    ADD CONSTRAINT passkey_credentials_credential_id_key UNIQUE (credential_id);


--
-- Name: passkey_credentials passkey_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkey_credentials
    ADD CONSTRAINT passkey_credentials_pkey PRIMARY KEY (passkey_id);


--
-- Name: passkey_login_sessions passkey_login_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkey_login_sessions
    ADD CONSTRAINT passkey_login_sessions_session_id_key UNIQUE (session_id);


--
-- Name: passkeys passkeys_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkeys
    ADD CONSTRAINT passkeys_pkey PRIMARY KEY (id);


--
-- Name: public_collection_tokens public_collection_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_collection_tokens
    ADD CONSTRAINT public_collection_tokens_pkey PRIMARY KEY (id);


--
-- Name: push_tokens push_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.push_tokens
    ADD CONSTRAINT push_tokens_pkey PRIMARY KEY (fcm_token);


--
-- Name: queue queue_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.queue
    ADD CONSTRAINT queue_pkey PRIMARY KEY (queue_id);


--
-- Name: referral_codes referral_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.referral_codes
    ADD CONSTRAINT referral_codes_pkey PRIMARY KEY (code);


--
-- Name: remote_store remote_store_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.remote_store
    ADD CONSTRAINT remote_store_pkey PRIMARY KEY (user_id, key_name);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: srp_auth srp_auth_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.srp_auth
    ADD CONSTRAINT srp_auth_pkey PRIMARY KEY (user_id);


--
-- Name: srp_auth srp_auth_srp_user_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.srp_auth
    ADD CONSTRAINT srp_auth_srp_user_id_key UNIQUE (srp_user_id);


--
-- Name: srp_sessions srp_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.srp_sessions
    ADD CONSTRAINT srp_sessions_pkey PRIMARY KEY (id);


--
-- Name: storage_bonus storage_bonus_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.storage_bonus
    ADD CONSTRAINT storage_bonus_pkey PRIMARY KEY (bonus_id);


--
-- Name: subscription_logs subscription_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscription_logs
    ADD CONSTRAINT subscription_logs_pkey PRIMARY KEY (log_id);


--
-- Name: subscriptions subscription_user_id_unique_constraint_index; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscription_user_id_unique_constraint_index UNIQUE (user_id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (subscription_id);


--
-- Name: task_lock task_lock_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.task_lock
    ADD CONSTRAINT task_lock_pkey PRIMARY KEY (task_name);


--
-- Name: temp_objects temp_object_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.temp_objects
    ADD CONSTRAINT temp_object_keys_pkey PRIMARY KEY (object_key);


--
-- Name: temp_srp_setup temp_srp_setup_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.temp_srp_setup
    ADD CONSTRAINT temp_srp_setup_pkey PRIMARY KEY (id);


--
-- Name: temp_two_factor temp_two_factor_two_factor_secret_hash_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.temp_two_factor
    ADD CONSTRAINT temp_two_factor_two_factor_secret_hash_key UNIQUE (two_factor_secret_hash);


--
-- Name: tokens tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT tokens_token_key UNIQUE (token);


--
-- Name: trash trash_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.trash
    ADD CONSTRAINT trash_pkey PRIMARY KEY (file_id);


--
-- Name: two_factor_recovery two_factor_recovery_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor_recovery
    ADD CONSTRAINT two_factor_recovery_pkey PRIMARY KEY (user_id);


--
-- Name: two_factor_sessions two_factor_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor_sessions
    ADD CONSTRAINT two_factor_sessions_session_id_key UNIQUE (session_id);


--
-- Name: two_factor two_factor_two_factor_secret_hash_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor
    ADD CONSTRAINT two_factor_two_factor_secret_hash_key UNIQUE (two_factor_secret_hash);


--
-- Name: two_factor two_factor_user_id_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor
    ADD CONSTRAINT two_factor_user_id_key UNIQUE (user_id);


--
-- Name: public_collection_access_history unique_access_sid_ip_ua; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_collection_access_history
    ADD CONSTRAINT unique_access_sid_ip_ua UNIQUE (share_id, ip, user_agent);


--
-- Name: collection_files unique_collection_files_cid_fid; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_files
    ADD CONSTRAINT unique_collection_files_cid_fid UNIQUE (collection_id, file_id);


--
-- Name: embeddings unique_embeddings_file_id_model; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.embeddings
    ADD CONSTRAINT unique_embeddings_file_id_model UNIQUE (file_id, model);


--
-- Name: otts unique_otts_emailhash_app_ott; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.otts
    ADD CONSTRAINT unique_otts_emailhash_app_ott UNIQUE (ott, app, email_hash);


--
-- Name: public_abuse_report unique_report_sid_ip_ua; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_abuse_report
    ADD CONSTRAINT unique_report_sid_ip_ua UNIQUE (share_id, ip, user_agent);


--
-- Name: emergency_contact unique_user_emergency_contact; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_contact
    ADD CONSTRAINT unique_user_emergency_contact UNIQUE (user_id, emergency_contact_id);


--
-- Name: usage usage_user_id_unique_constraint_index; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.usage
    ADD CONSTRAINT usage_user_id_unique_constraint_index UNIQUE (user_id);


--
-- Name: users users_email_hash_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_hash_key UNIQUE (email_hash);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: webauthn_sessions webauthn_sessions_challenge_key; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.webauthn_sessions
    ADD CONSTRAINT webauthn_sessions_challenge_key UNIQUE (challenge);


--
-- Name: webauthn_sessions webauthn_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.webauthn_sessions
    ADD CONSTRAINT webauthn_sessions_pkey PRIMARY KEY (id);


--
-- Name: authenticator_entity_updated_at_time_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX authenticator_entity_updated_at_time_index ON public.authenticator_entity USING btree (user_id, updated_at);


--
-- Name: casting_code_unique_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX casting_code_unique_idx ON public.casting USING btree (code) WHERE (is_deleted = false);


--
-- Name: collection_files_collection_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX collection_files_collection_id_index ON public.collection_files USING btree (collection_id);


--
-- Name: collection_files_file_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX collection_files_file_id_index ON public.collection_files USING btree (file_id);


--
-- Name: collection_shares_to_user_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX collection_shares_to_user_id_index ON public.collection_shares USING btree (to_user_id);


--
-- Name: collections_favorites_constraint_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX collections_favorites_constraint_index ON public.collections USING btree (owner_id) WHERE (type = 'favorites'::text);


--
-- Name: collections_owner_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX collections_owner_id_index ON public.collections USING btree (owner_id);


--
-- Name: collections_uncategorized_constraint_index_v2; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX collections_uncategorized_constraint_index_v2 ON public.collections USING btree (owner_id, app) WHERE (type = 'uncategorized'::text);


--
-- Name: embeddings_owner_id_updated_at_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX embeddings_owner_id_updated_at_index ON public.embeddings USING btree (owner_id, updated_at);


--
-- Name: entity_data_updated_at_time_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX entity_data_updated_at_time_index ON public.entity_data USING btree (user_id, updated_at);


--
-- Name: files_owner_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX files_owner_id_index ON public.files USING btree (owner_id);


--
-- Name: files_updation_time_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX files_updation_time_index ON public.files USING btree (updation_time);


--
-- Name: fk_families_admin_id; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX fk_families_admin_id ON public.families USING btree (admin_id);


--
-- Name: idx_emergency_contact_id; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_emergency_contact_id ON public.emergency_contact USING btree (emergency_contact_id);


--
-- Name: idx_emergency_recovery_limit_active_recovery; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX idx_emergency_recovery_limit_active_recovery ON public.emergency_recovery USING btree (user_id, emergency_contact_id, status) WHERE (status = ANY (ARRAY['WAITING'::text, 'READY'::text]));


--
-- Name: idx_emergency_recovery_next_reminder_at; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_emergency_recovery_next_reminder_at ON public.emergency_recovery USING btree (next_reminder_at);


--
-- Name: idx_emergency_recovery_user_id; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_emergency_recovery_user_id ON public.emergency_recovery USING btree (user_id);


--
-- Name: idx_file_data_pending_sync_locked_till; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_file_data_pending_sync_locked_till ON public.file_data USING btree (is_deleted, sync_locked_till) WHERE (pending_sync = true);


--
-- Name: idx_file_data_user_type_deleted; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_file_data_user_type_deleted ON public.file_data USING btree (user_id, data_type, is_deleted) INCLUDE (size);


--
-- Name: idx_queue_created_at_non_deleted; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX idx_queue_created_at_non_deleted ON public.queue USING btree (queue_name, created_at) WHERE (is_deleted = false);


--
-- Name: name_and_item_unique_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX name_and_item_unique_index ON public.queue USING btree (queue_name, item);


--
-- Name: object_copies_scw_null_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX object_copies_scw_null_index ON public.object_copies USING btree (scw) WHERE ((scw IS NULL) AND (want_scw = true));


--
-- Name: object_copies_wasabi_null_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX object_copies_wasabi_null_index ON public.object_copies USING btree (wasabi) WHERE ((wasabi IS NULL) AND (want_wasabi = true));


--
-- Name: otts_email_hash_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX otts_email_hash_index ON public.otts USING btree (email_hash);


--
-- Name: public_abuse_share_id_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX public_abuse_share_id_idx ON public.public_abuse_report USING btree (share_id);


--
-- Name: public_access_share_id_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX public_access_share_id_idx ON public.public_collection_access_history USING btree (share_id);


--
-- Name: public_access_tokens_unique_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX public_access_tokens_unique_idx ON public.public_collection_tokens USING btree (access_token);


--
-- Name: public_active_collection_unique_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX public_active_collection_unique_idx ON public.public_collection_tokens USING btree (collection_id, is_disabled) WHERE (is_disabled = false);


--
-- Name: push_tokens_last_notified_at_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX push_tokens_last_notified_at_index ON public.push_tokens USING btree (last_notified_at);


--
-- Name: q_name_create_and_is_deleted_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX q_name_create_and_is_deleted_index ON public.queue USING btree (queue_name, created_at, is_deleted);


--
-- Name: referral_codes_user_id_is_active_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX referral_codes_user_id_is_active_idx ON public.referral_codes USING btree (user_id, is_active) WHERE (is_active = true);


--
-- Name: referral_tracking_invitee_id_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX referral_tracking_invitee_id_idx ON public.referral_tracking USING btree (invitee_id);


--
-- Name: storage_bonus_user_id_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX storage_bonus_user_id_idx ON public.storage_bonus USING btree (user_id);


--
-- Name: sub_original_txn_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX sub_original_txn_id_index ON public.subscriptions USING btree (original_transaction_id) WHERE ((original_transaction_id IS NOT NULL) AND (original_transaction_id <> 'none'::text));


--
-- Name: subscriptions_expiry_time_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX subscriptions_expiry_time_index ON public.subscriptions USING btree (expiry_time);


--
-- Name: subscriptions_user_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX subscriptions_user_id_index ON public.subscriptions USING btree (user_id);


--
-- Name: task_lock_locked_until; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX task_lock_locked_until ON public.task_lock USING btree (lock_until);


--
-- Name: tokens_user_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX tokens_user_id_index ON public.tokens USING btree (user_id);


--
-- Name: trash_delete_by_idx; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX trash_delete_by_idx ON public.trash USING btree (delete_by) WHERE ((is_deleted IS FALSE) AND (is_restored IS FALSE));


--
-- Name: trash_updated_at_time_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX trash_updated_at_time_index ON public.trash USING btree (updated_at);


--
-- Name: trash_user_id_and_updated_at_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX trash_user_id_and_updated_at_index ON public.trash USING btree (user_id, updated_at);


--
-- Name: uidx_families_member_mapping; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX uidx_families_member_mapping ON public.families USING btree (admin_id, member_id);


--
-- Name: uidx_one_family_check; Type: INDEX; Schema: public; Owner: pguser
--

CREATE UNIQUE INDEX uidx_one_family_check ON public.families USING btree (member_id, status) WHERE (status = ANY (ARRAY['ACCEPTED'::text, 'SELF'::text]));


--
-- Name: usage_user_id_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX usage_user_id_index ON public.usage USING btree (user_id);


--
-- Name: users_email_hash_index; Type: INDEX; Schema: public; Owner: pguser
--

CREATE INDEX users_email_hash_index ON public.users USING btree (email_hash);


--
-- Name: file_data check_no_common_entries; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER check_no_common_entries BEFORE INSERT OR UPDATE ON public.file_data FOR EACH ROW EXECUTE FUNCTION public.ensure_no_common_entries();


--
-- Name: authenticator_entity trigger_authenticator_key_updated_time_on_authenticator_entity_; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER trigger_authenticator_key_updated_time_on_authenticator_entity_ AFTER INSERT OR UPDATE ON public.authenticator_entity FOR EACH ROW EXECUTE FUNCTION public.fn_update_authenticator_key_updated_at_via_updated_at();


--
-- Name: public_collection_tokens trigger_collection_updation_time_on_collection_tokens_updated; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER trigger_collection_updation_time_on_collection_tokens_updated AFTER INSERT OR UPDATE ON public.public_collection_tokens FOR EACH ROW EXECUTE FUNCTION public.fn_update_collections_updation_time_using_update_at();


--
-- Name: entity_data trigger_entity_key_on_entity_data_updation; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER trigger_entity_key_on_entity_data_updation AFTER INSERT OR UPDATE ON public.entity_data FOR EACH ROW EXECUTE FUNCTION public.fn_update_entity_key_updated_at_via_updated_at();


--
-- Name: authenticator_entity update_authenticator_entity_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_authenticator_entity_updated_at BEFORE UPDATE ON public.authenticator_entity FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: families update_emergency_conctact_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_emergency_conctact_updated_at BEFORE UPDATE ON public.families FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: families update_emergency_recovery_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_emergency_recovery_updated_at BEFORE UPDATE ON public.families FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: entity_data update_entity_data_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_entity_data_updated_at BEFORE UPDATE ON public.entity_data FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: families update_families_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_families_updated_at BEFORE UPDATE ON public.families FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: object_keys update_object_keys_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_object_keys_updated_at BEFORE UPDATE ON public.object_keys FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: public_collection_tokens update_public_collection_tokens_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_public_collection_tokens_updated_at BEFORE UPDATE ON public.public_collection_tokens FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: push_tokens update_push_tokens_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_push_tokens_updated_at BEFORE UPDATE ON public.push_tokens FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: queue update_queue_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_queue_updated_at BEFORE UPDATE ON public.queue FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: remote_store update_remote_store_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_remote_store_updated_at BEFORE UPDATE ON public.remote_store FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: srp_auth update_srp_auth_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_srp_auth_updated_at BEFORE UPDATE ON public.srp_auth FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: srp_sessions update_srp_sessions_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_srp_sessions_updated_at BEFORE UPDATE ON public.srp_sessions FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: trash update_trash_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_trash_updated_at BEFORE UPDATE ON public.trash FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: two_factor_recovery update_two_factor_recovery_updated_at; Type: TRIGGER; Schema: public; Owner: pguser
--

CREATE TRIGGER update_two_factor_recovery_updated_at BEFORE UPDATE ON public.two_factor_recovery FOR EACH ROW EXECUTE FUNCTION public.trigger_updated_at_microseconds_column();


--
-- Name: authenticator_key fk_authenticator_key_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.authenticator_key
    ADD CONSTRAINT fk_authenticator_key_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: authenticator_entity fk_authenticator_key_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.authenticator_entity
    ADD CONSTRAINT fk_authenticator_key_user_id FOREIGN KEY (user_id) REFERENCES public.authenticator_key(user_id) ON DELETE CASCADE;


--
-- Name: collection_files fk_collection_files_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_files
    ADD CONSTRAINT fk_collection_files_collection_id FOREIGN KEY (collection_id) REFERENCES public.collections(collection_id) ON DELETE CASCADE;


--
-- Name: collection_files fk_collection_files_file_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_files
    ADD CONSTRAINT fk_collection_files_file_id FOREIGN KEY (file_id) REFERENCES public.files(file_id) ON DELETE CASCADE;


--
-- Name: collection_shares fk_collection_shares_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_shares
    ADD CONSTRAINT fk_collection_shares_collection_id FOREIGN KEY (collection_id) REFERENCES public.collections(collection_id) ON DELETE CASCADE;


--
-- Name: collection_shares fk_collection_shares_from_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_shares
    ADD CONSTRAINT fk_collection_shares_from_user_id FOREIGN KEY (from_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: collection_shares fk_collection_shares_to_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collection_shares
    ADD CONSTRAINT fk_collection_shares_to_user_id FOREIGN KEY (to_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: collections fk_collections_owner_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT fk_collections_owner_id FOREIGN KEY (owner_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: embeddings fk_embeddings_file_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.embeddings
    ADD CONSTRAINT fk_embeddings_file_id FOREIGN KEY (file_id) REFERENCES public.files(file_id) ON DELETE CASCADE;


--
-- Name: emergency_contact fk_emergency_contact_emergency_contact_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_contact
    ADD CONSTRAINT fk_emergency_contact_emergency_contact_id FOREIGN KEY (emergency_contact_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: emergency_contact fk_emergency_contact_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_contact
    ADD CONSTRAINT fk_emergency_contact_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: emergency_recovery fk_emergency_recovery_emergency_contact_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_recovery
    ADD CONSTRAINT fk_emergency_recovery_emergency_contact_id FOREIGN KEY (emergency_contact_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: emergency_recovery fk_emergency_recovery_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.emergency_recovery
    ADD CONSTRAINT fk_emergency_recovery_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: entity_key fk_entity_key_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.entity_key
    ADD CONSTRAINT fk_entity_key_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: entity_data fk_entity_key_user_id_and_type; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.entity_data
    ADD CONSTRAINT fk_entity_key_user_id_and_type FOREIGN KEY (user_id, type) REFERENCES public.entity_key(user_id, type) ON DELETE CASCADE;


--
-- Name: families fk_family_admin_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.families
    ADD CONSTRAINT fk_family_admin_id FOREIGN KEY (admin_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: files fk_files_owner_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT fk_files_owner_id FOREIGN KEY (owner_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: key_attributes fk_key_attributes_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.key_attributes
    ADD CONSTRAINT fk_key_attributes_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: notification_history fk_notification_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.notification_history
    ADD CONSTRAINT fk_notification_history_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: object_copies fk_object_copies_object_key; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.object_copies
    ADD CONSTRAINT fk_object_copies_object_key FOREIGN KEY (object_key) REFERENCES public.object_keys(object_key) ON DELETE CASCADE;


--
-- Name: object_keys fk_object_keys_file_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.object_keys
    ADD CONSTRAINT fk_object_keys_file_id FOREIGN KEY (file_id) REFERENCES public.files(file_id) ON DELETE CASCADE;


--
-- Name: passkey_credentials fk_passkey_credentials_passkey_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkey_credentials
    ADD CONSTRAINT fk_passkey_credentials_passkey_id FOREIGN KEY (passkey_id) REFERENCES public.passkeys(id) ON DELETE CASCADE;


--
-- Name: passkey_login_sessions fk_passkey_login_sessions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkey_login_sessions
    ADD CONSTRAINT fk_passkey_login_sessions_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: passkeys fk_passkeys_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.passkeys
    ADD CONSTRAINT fk_passkeys_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: public_abuse_report fk_public_abuse_report_token_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_abuse_report
    ADD CONSTRAINT fk_public_abuse_report_token_id FOREIGN KEY (share_id) REFERENCES public.public_collection_tokens(id) ON DELETE CASCADE;


--
-- Name: public_collection_access_history fk_public_history_token_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_collection_access_history
    ADD CONSTRAINT fk_public_history_token_id FOREIGN KEY (share_id) REFERENCES public.public_collection_tokens(id) ON DELETE CASCADE;


--
-- Name: public_collection_tokens fk_public_tokens_collection_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.public_collection_tokens
    ADD CONSTRAINT fk_public_tokens_collection_id FOREIGN KEY (collection_id) REFERENCES public.collections(collection_id) ON DELETE CASCADE;


--
-- Name: push_tokens fk_push_tokens_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.push_tokens
    ADD CONSTRAINT fk_push_tokens_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: remote_store fk_remote_store_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.remote_store
    ADD CONSTRAINT fk_remote_store_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: two_factor_sessions fk_sessions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor_sessions
    ADD CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: srp_auth fk_srp_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.srp_auth
    ADD CONSTRAINT fk_srp_auth_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: subscription_logs fk_subscription_logs_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscription_logs
    ADD CONSTRAINT fk_subscription_logs_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: subscriptions fk_subscriptions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT fk_subscriptions_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: temp_srp_setup fk_temp_srp_setup_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.temp_srp_setup
    ADD CONSTRAINT fk_temp_srp_setup_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: tokens fk_tokens_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT fk_tokens_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: trash fk_trash_keys_collection_files; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.trash
    ADD CONSTRAINT fk_trash_keys_collection_files FOREIGN KEY (file_id, collection_id) REFERENCES public.collection_files(file_id, collection_id);


--
-- Name: temp_two_factor fk_two_factor_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.temp_two_factor
    ADD CONSTRAINT fk_two_factor_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: two_factor fk_two_factor_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.two_factor
    ADD CONSTRAINT fk_two_factor_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: usage fk_usage_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.usage
    ADD CONSTRAINT fk_usage_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: webauthn_sessions fk_webauthn_sessions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pguser
--

ALTER TABLE ONLY public.webauthn_sessions
    ADD CONSTRAINT fk_webauthn_sessions_user_id FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

