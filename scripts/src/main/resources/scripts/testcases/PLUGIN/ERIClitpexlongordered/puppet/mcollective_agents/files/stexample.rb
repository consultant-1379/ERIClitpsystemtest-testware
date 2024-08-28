module MCollective
  module Agent
    class Stexample<RPC::Agent
      # Basic echo example
      action "my_action" do
        cmd = "echo  \"#{request[:service]}\" "
        reply[:status] = run("#{cmd}",
                              :stdout => :out,
                              :stderr => :err,
                              :chomp => true)

      end
    end
  end
end

