"""
Docstring for documentation.monitoring

# MONITORING-----

SMTP monitoring is very important fro newer email servers as,
they have to maintain the incoming and outgoing emails realiably.

# TYPES OF FAILURES IN SMTP --- 

There are two types of email delivery failures 
that you may encounter when sending outbound email — synchronous and asynchronous failures.

  -- Synchronous Failure:
            Synchronous failures happen when the remote mail server rejects the message. 
            This happens during the initial conversation between the SMTP server and the receiving mail server.
            
  -- ASynchronous Failure:
            An asynchronous failure occurs when the remote mail server accepts the message 
            and then later returns it by sending an NDR (Non Delivery Report) to the return path of the message. 
            
            Since the receiving mail server initially accepted the message, 
            it's easy to believe that the message was successfully delivered. 
            
            It is not until we later receive a failure notification from the remote server 
            that we know that the outbound message has failed. 
            
            This is known as an email bounce, which can be either hard or soft.

            Many people make the mistake of assuming that all failures are bounces. 
            Technically speaking, synchronous failures are not bounces.


# ERROR TYPES IN SMTP ---

  -- Permanent Errors:
    
            A permanent error, or permanent failure is exactly how it sounds — the 
            message was returned by the recipient mail server and 
            no further attempt will be made to deliver the message.
    
            Below are some standard error messages that indicate that a domain or account does not exist:

                -> 554 delivery error: This user doesn’t have an account
                -> 550 5.1.1:  Mailbox does not exist
                -> 500:  No such user
                -> 553 5.3.0:Addressee unknown
                -> 550 Requested action not taken: Mailbox unavailable
                -> Name service error for baddomain.com Type=A : Host not found 
                    (This error means that the DNS server returned an error specifically saying 
                    that the domain does not exist).

  -- Temporary Errors:
            ....
            
            
            
# Email Greylisting

"""

