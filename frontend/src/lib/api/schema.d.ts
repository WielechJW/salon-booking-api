export interface paths {
    "/services": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Services */
        get: operations["get_services_services_get"];
        put?: never;
        /** Create Service */
        post: operations["create_service_services_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/services/{service_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Service */
        get: operations["get_service_services__service_id__get"];
        /** Update Service */
        put: operations["update_service_services__service_id__put"];
        post?: never;
        /** Delete Service */
        delete: operations["delete_service_services__service_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employees */
        get: operations["get_employees_employees_get"];
        put?: never;
        /** Create Employee */
        post: operations["create_employee_employees_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employee */
        get: operations["get_employee_employees__employee_id__get"];
        /** Update Employee */
        put: operations["update_employee_employees__employee_id__put"];
        post?: never;
        /** Delete Employee */
        delete: operations["delete_employee_employees__employee_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/services/{service_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign Service To Employee */
        post: operations["assign_service_to_employee_employees__employee_id__services__service_id__post"];
        /** Remove Service From Employee */
        delete: operations["remove_service_from_employee_employees__employee_id__services__service_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/services": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employee Services */
        get: operations["get_employee_services_employees__employee_id__services_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/account": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Assign Account */
        put: operations["assign_account_employees__employee_id__account_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/appointments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Appointments */
        get: operations["get_appointments_appointments_get"];
        put?: never;
        /** Create Appointment */
        post: operations["create_appointment_appointments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/appointments/{appointment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Appointment */
        get: operations["get_appointment_appointments__appointment_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/appointments/{appointment_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Appointment Status */
        patch: operations["update_appointment_status_appointments__appointment_id__status_patch"];
        trace?: never;
    };
    "/employees/{employee_id}/schedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employee Schedule */
        get: operations["get_employee_schedule_employees__employee_id__schedule_get"];
        /** Update Schedule */
        put: operations["update_schedule_employees__employee_id__schedule_put"];
        /** Create Schedule */
        post: operations["create_schedule_employees__employee_id__schedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/availability": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employee Availability */
        get: operations["get_employee_availability_employees__employee_id__availability_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/availability": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Service Availability */
        get: operations["get_service_availability_availability_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/time-off": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Employee Time Offs */
        get: operations["get_employee_time_offs_employees__employee_id__time_off_get"];
        put?: never;
        /** Create Time Off */
        post: operations["create_time_off_employees__employee_id__time_off_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/employees/{employee_id}/time-off/{time_off_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Time Off */
        put: operations["update_time_off_employees__employee_id__time_off__time_off_id__put"];
        post?: never;
        /** Delete Time Off */
        delete: operations["delete_time_off_employees__employee_id__time_off__time_off_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_users_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/me/appointments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get My Appointments */
        get: operations["get_my_appointments_users_me_appointments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Root */
        get: operations["root__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/salon": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Salon Info */
        get: operations["get_salon_info_salon_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** Appointment */
        Appointment: {
            /** Employee Id */
            employee_id: number;
            /** Service Id */
            service_id: number;
            /**
             * Start At
             * Format: date-time
             */
            start_at: string;
            /** Client Id */
            client_id?: number | null;
            /** Client Name */
            client_name: string;
            /**
             * Client Email
             * Format: email
             */
            client_email: string;
            /** Client Phone */
            client_phone: string;
        };
        /** AppointmentResponse */
        AppointmentResponse: {
            /** Id */
            id: number;
            /** Client Id */
            client_id: number | null;
            /** Employee Id */
            employee_id: number;
            /** Service Id */
            service_id: number;
            /**
             * Start At
             * Format: date-time
             */
            start_at: string;
            /** Client Name */
            client_name: string;
            /** Client Email */
            client_email: string;
            /** Client Phone */
            client_phone: string;
            /** Duration Minutes */
            duration_minutes: number;
            /** Price */
            price: number;
            /**
             * End At
             * Format: date-time
             */
            end_at: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "confirmed" | "cancelled" | "completed";
        };
        /** AppointmentStatusUpdate */
        AppointmentStatusUpdate: {
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "confirmed" | "cancelled" | "completed";
        };
        /** AvailabilityResponse */
        AvailabilityResponse: {
            /** Employee Id */
            employee_id: number;
            /** Service Id */
            service_id: number;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Available Slots */
            available_slots: string[];
        };
        /** Body_login_auth_login_post */
        Body_login_auth_login_post: {
            /** Grant Type */
            grant_type?: string | null;
            /** Username */
            username: string;
            /**
             * Password
             * Format: password
             */
            password: string;
            /**
             * Scope
             * @default
             */
            scope: string;
            /** Client Id */
            client_id?: string | null;
            /**
             * Client Secret
             * Format: password
             */
            client_secret?: string | null;
        };
        /** Employee */
        Employee: {
            /** Name */
            name: string;
        };
        /** EmployeeAccountAssignment */
        EmployeeAccountAssignment: {
            /** User Id */
            user_id: number;
        };
        /** EmployeeResponse */
        EmployeeResponse: {
            /** Name */
            name: string;
            /** Id */
            id: number;
        };
        /** EmployeeTimeOff */
        EmployeeTimeOff: {
            /**
             * Start At
             * Format: date-time
             */
            start_at: string;
            /**
             * End At
             * Format: date-time
             */
            end_at: string;
            /** Reason */
            reason: string;
        };
        /** EmployeeTimeOffResponse */
        EmployeeTimeOffResponse: {
            /**
             * Start At
             * Format: date-time
             */
            start_at: string;
            /**
             * End At
             * Format: date-time
             */
            end_at: string;
            /** Reason */
            reason: string;
            /** Id */
            id: number;
            /** Employee Id */
            employee_id: number;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** SalonInfo */
        SalonInfo: {
            /** Timezone */
            timezone: string;
        };
        /** Schedule */
        Schedule: {
            /** Day Of Week */
            day_of_week: number;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /**
             * End Time
             * Format: time
             */
            end_time: string;
        };
        /** ScheduleResponse */
        ScheduleResponse: {
            /** Day Of Week */
            day_of_week: number;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /**
             * End Time
             * Format: time
             */
            end_time: string;
            /** Id */
            id: number;
            /** Employee Id */
            employee_id: number;
        };
        /** Service */
        Service: {
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Duration Minutes */
            duration_minutes: number;
            /** Price */
            price: number | string;
        };
        /** ServiceAvailabilitySlotResponse */
        ServiceAvailabilitySlotResponse: {
            /** Employee Id */
            employee_id: number;
            /** Employee Name */
            employee_name: string;
            /**
             * Start At
             * Format: date-time
             */
            start_at: string;
            /**
             * End At
             * Format: date-time
             */
            end_at: string;
        };
        /** ServiceResponse */
        ServiceResponse: {
            /** Name */
            name: string;
            /** Description */
            description: string;
            /** Duration Minutes */
            duration_minutes: number;
            /** Price */
            price: number;
            /** Id */
            id: number;
        };
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
        };
        /** UserRegister */
        UserRegister: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * Format: password
             */
            password: string;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Phone */
            phone: string;
        };
        /** UserResponse */
        UserResponse: {
            /** Id */
            id: number;
            /** Email */
            email: string;
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Phone */
            phone: string;
            /**
             * Role
             * @enum {string}
             */
            role: "CLIENT" | "EMPLOYEE" | "ADMIN";
            /** Is Active */
            is_active: boolean;
            /** Employee Id */
            employee_id?: number | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    get_services_services_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceResponse"][];
                };
            };
        };
    };
    create_service_services_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Service"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_service_services__service_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                service_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_service_services__service_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                service_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Service"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_service_services__service_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                service_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employees_employees_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeResponse"][];
                };
            };
        };
    };
    create_employee_employees_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Employee"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employee_employees__employee_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_employee_employees__employee_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Employee"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_employee_employees__employee_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_service_to_employee_employees__employee_id__services__service_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
                service_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_service_from_employee_employees__employee_id__services__service_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
                service_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employee_services_employees__employee_id__services_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_account_employees__employee_id__account_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmployeeAccountAssignment"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_appointments_appointments_get: {
        parameters: {
            query?: {
                employee_id?: number | null;
                status?: ("pending" | "confirmed" | "cancelled" | "completed") | null;
                date_from?: string | null;
                date_to?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    /** @description Number of matching appointments visible to the user */
                    "X-Total-Count"?: number;
                    "X-Limit"?: number;
                    "X-Offset"?: number;
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppointmentResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_appointment_appointments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Appointment"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppointmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_appointment_appointments__appointment_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                appointment_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppointmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_appointment_status_appointments__appointment_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                appointment_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AppointmentStatusUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppointmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employee_schedule_employees__employee_id__schedule_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScheduleResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_schedule_employees__employee_id__schedule_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Schedule"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScheduleResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_schedule_employees__employee_id__schedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Schedule"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScheduleResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employee_availability_employees__employee_id__availability_get: {
        parameters: {
            query: {
                date: string;
                service_id: number;
            };
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AvailabilityResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_service_availability_availability_get: {
        parameters: {
            query: {
                date: string;
                service_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ServiceAvailabilitySlotResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_employee_time_offs_employees__employee_id__time_off_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeTimeOffResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_time_off_employees__employee_id__time_off_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmployeeTimeOff"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeTimeOffResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_time_off_employees__employee_id__time_off__time_off_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
                time_off_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmployeeTimeOff"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EmployeeTimeOffResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_time_off_employees__employee_id__time_off__time_off_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
                time_off_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserRegister"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/x-www-form-urlencoded": components["schemas"]["Body_login_auth_login_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_users_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
        };
    };
    get_my_appointments_users_me_appointments_get: {
        parameters: {
            query?: {
                employee_id?: number | null;
                status?: ("pending" | "confirmed" | "cancelled" | "completed") | null;
                date_from?: string | null;
                date_to?: string | null;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    /** @description Number of matching appointments visible to the user */
                    "X-Total-Count"?: number;
                    "X-Limit"?: number;
                    "X-Offset"?: number;
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AppointmentResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    root__get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_salon_info_salon_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SalonInfo"];
                };
            };
        };
    };
}
