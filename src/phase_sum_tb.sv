`include "rns_types.sv"

module phase_sum_tb;

    out_t out;
    rns_t a, b;

    phase_sum dut (
        .out(out),
        .a(a),
        .b(b)
    );

    longint M = 64'sd2214408306;
    int moduli[6] = '{2, 3, 11, 23, 31, 47057};
    int errors = 0;
    int tests = 0;

    task automatic set_rns(input longint n, output rns_t r);
        /* verilator lint_off WIDTHTRUNC */
        r.first  = n % 2;
        r.second = n % 3;
        r.third  = n % 11;
        r.fourth = n % 23;
        r.fifth  = n % 31;
        r.sixth  = n % 47057;
        /* verilator lint_on WIDTHTRUNC */
    endtask

    task automatic check(input longint a_val, input longint b_val);
        logic expected_lt, expected_eq, expected_gt;
        tests++;

        expected_lt = (a_val < b_val);
        expected_eq = (a_val == b_val);
        expected_gt = (a_val > b_val);

        if (out.lt !== expected_lt || out.eq !== expected_eq || out.gt !== expected_gt) begin
            $display("FAIL: a=%0d b=%0d exp=%b%b%b got=%b%b%b",
                a_val, b_val, expected_lt, expected_eq, expected_gt,
                out.lt, out.eq, out.gt);
            errors++;
        end
    endtask

    initial begin
        longint n, m;

        $display("Test 1: exhaustive adjacent pairs (0..99999)");
        for (n = 0; n < 10000000; n++) begin
            set_rns(n, a);
            set_rns(n + 1, b);
            #1;
            check(n, n + 1);
        end
        $display("  done, errors=%0d", errors);

        $display("Test 2: exhaustive adjacent pairs near M/2");
        for (n = M/2 - 50000; n < M/2 + 50000; n++) begin
            set_rns(n, a);
            set_rns(n + 1, b);
            #1;
            check(n, n + 1);
        end
        $display("  done, errors=%0d", errors);

        $display("Test 3: exhaustive adjacent pairs near M");
        for (n = M - 100001; n < M - 1; n++) begin
            set_rns(n, a);
            set_rns(n + 1, b);
            #1;
            check(n, n + 1);
        end
        $display("  done, errors=%0d", errors);

        $display("Test 4: all values 0..999 vs all values 0..999");
        for (n = 0; n < 1000; n++) begin
            for (m = 0; m < 1000; m++) begin
                set_rns(n, a);
                set_rns(m, b);
                #1;
                check(n, m);
            end
        end
        $display("  done, errors=%0d", errors);

        $display("Test 5: random pairs");
        repeat (1_000_000) begin
            /* verilator lint_off WIDTHEXPAND */
            n = $urandom_range(0, 32'sd2147483647);
            m = $urandom_range(0, 32'sd2147483647);
            /* verilator lint_on WIDTHEXPAND */
            set_rns(n, a);
            set_rns(m, b);
            #1;
            check(n, m);
        end
        $display("  done, errors=%0d", errors);

        $display("Test 6: powers of 2 vs neighbors");
        for (int i = 0; i < 31; i++) begin
            n = 1 << i;
            if (n < M) begin
                if (n > 0) begin
                    set_rns(n - 1, a);
                    set_rns(n, b);
                    #1;
                    check(n - 1, n);
                end
                if (n + 1 < M) begin
                    set_rns(n, a);
                    set_rns(n + 1, b);
                    #1;
                    check(n, n + 1);
                end
            end
        end
        $display("  done, errors=%0d", errors);

        $display("SUMMARY: %0d tests, %0d errors", tests, errors);
        if (errors == 0) $display("ALL PASSED");
        else begin
            $display("FAILURES DETECTED");
            $finish(1);
        end
        $finish;
    end

endmodule
