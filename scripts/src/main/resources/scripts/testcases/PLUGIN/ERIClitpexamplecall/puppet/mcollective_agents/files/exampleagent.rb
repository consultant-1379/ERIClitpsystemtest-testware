module MCollective
  module Agent
    class Exampleagent<RPC::Agent
      # Basic echo example
      action "serve_as_example" do
        cmd = "echo  \"#{request[:echo_string]}\" "
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)

      end
    end
  end
end

